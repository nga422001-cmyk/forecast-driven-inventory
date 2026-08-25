"""
Multi-dimensional sensitivity sweep.

The purpose here is not to show that a policy survives changing assumptions. It
is to measure how often the *conclusion* survives — that is, in what fraction of
plausible parameter settings the better forecast is actually the cheaper one.

Choice of sweep dimensions matters. Under a cost-minimising formulation subject
to a service constraint, the carrying rate is a pure multiplier: it scales both
models' costs identically and therefore cannot change which is cheaper. Sweeping
it produces larger tables but no additional information. The dimensions swept
here are the ones that can change the answer:

    lead time          -> sets the protection period, over which errors either
                          cancel or accumulate
    service target     -> moves the binding constraint from the centre of the
                          error distribution to its tail
    service definition -> cycle service counts stockout events, fill rate
                          measures their depth; a forecast can win on one and
                          lose on the other
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import backtest, inventory, simulate


def sweep_lead_times(
    panel: pd.DataFrame,
    models: dict,
    lead_times,
    review_period: int,
    min_train: int,
    carrying_rate: float,
    grid: np.ndarray | None = None,
    warmup: int = 10,
) -> dict:
    """
    Re-run the whole pipeline once per lead time.

    Returns {lead_time: {"P", "decomp", "frontier"}}. Kept separate from the
    scoring step below so an expensive sweep is computed once and can then be
    interrogated at many service targets.
    """
    grid = np.arange(0.0, 3.51, 0.1) if grid is None else grid
    out = {}

    for lead_time in lead_times:
        P = review_period + lead_time
        plan = backtest.build_promo_plan(panel, P)
        bt = backtest.run_backtest(panel, plan, horizon=P,
                                   min_train=min_train, models=models)
        cum = inventory.protection_period_errors(bt, protection=P)

        out[lead_time] = {
            "P": P,
            "decomp": inventory.decompose_error(bt, cum, P),
            "frontier": simulate.build_frontier(
                bt, cum, lead_time=lead_time,
                carrying_rate=carrying_rate, grid=grid, warmup=warmup,
            ),
        }

    return out


def score_sweep(
    sweeps: dict,
    baseline: str,
    challenger: str,
    targets: dict[str, list[float]],
) -> pd.DataFrame:
    """
    Evaluate the challenger against the baseline at every (lead time, metric,
    target, store) combination.

    A combination is only scored when both models can reach the target; where
    one cannot, the comparison is undefined rather than a win.
    """
    rows = []

    for lead_time, res in sweeps.items():
        frontier = res["frontier"]
        for store in sorted(frontier["store"].unique()):
            for metric, target_list in targets.items():
                for target in target_list:
                    base = simulate.cost_at_service(
                        frontier, store, baseline, metric, target)
                    chal = simulate.cost_at_service(
                        frontier, store, challenger, metric, target)
                    rows.append({
                        "lead_time": lead_time,
                        "P": res["P"],
                        "store": store,
                        "metric": metric,
                        "target": target,
                        "cost_baseline": base,
                        "cost_challenger": chal,
                        "saving": base - chal,
                        "feasible": np.isfinite(base) and np.isfinite(chal),
                    })

    df = pd.DataFrame(rows)
    df["challenger_wins"] = df["feasible"] & (df["saving"] > 0)
    return df


def robustness_summary(scored: pd.DataFrame) -> pd.DataFrame:
    """
    Share of feasible parameter settings in which the challenger is cheaper.

    A value near 1 means the recommendation holds across the plausible parameter
    space. A value near 0.5 means the recommendation is a coin flip determined by
    assumptions the data cannot settle — which is itself the finding.
    """
    feasible = scored[scored["feasible"]]

    by_store = (
        feasible.groupby("store")["challenger_wins"]
        .agg(["sum", "count"])
        .rename(columns={"sum": "wins", "count": "settings"})
    )
    by_store["win_rate"] = by_store["wins"] / by_store["settings"]

    overall = pd.DataFrame({
        "wins": [feasible["challenger_wins"].sum()],
        "settings": [len(feasible)],
        "win_rate": [feasible["challenger_wins"].mean()],
    }, index=["overall"])
    overall.index.name = "store"

    return pd.concat([by_store, overall])
