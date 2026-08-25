"""
Simulation of a periodic-review (R, S) replenishment policy.

Computing safety stock from a formula is a promise; simulating the policy against
realised demand is the evidence. The formula assumes normally distributed,
independent errors and treats inventory as a static quantity. Inventory is in
fact a dynamic system in which orders overlap, and a stockout in one week changes
the position in the next.

Event sequence within each week, in order:
    1. receive any order arriving this week
    2. review stock and order up to S
    3. demand occurs and depletes on-hand stock

Ordering before demand matters. Reversing steps 2 and 3 lets the planner see the
week's sales before deciding, which no real planner can do, and inflates every
service metric that follows.
"""

from __future__ import annotations

import numpy as np
import pandas as pd


def simulate_policy(
    bt: pd.DataFrame,
    store,
    model: str,
    safety_stock: float,
    lead_time: int,
    warmup: int = 10,
) -> pd.Series:
    """
    Run one (R, S) policy over the backtested origins.

    Inventory is measured as the mean of start-of-week and end-of-week on-hand,
    approximating mid-week holding. Measuring end-of-week stock alone understates
    carrying cost by roughly half a replenishment cycle.
    """
    d = bt[(bt["store"] == store) & (bt["model"] == model)].sort_values(["origin", "h"])
    if d.empty:
        raise ValueError(f"No backtest rows for store={store!r} model={model!r}")

    order_up_to = d.groupby("origin")["y_pred"].sum() + safety_stock
    demand = d[d["h"] == 1].set_index("origin")["y_true"]
    origins = list(order_up_to.index)

    on_hand = float(order_up_to.iloc[0])
    pipeline: dict[int, float] = {}
    unmet_total = demand_total = 0.0
    stockout_weeks = scored = 0
    inventory = []

    for i, o in enumerate(origins):
        on_hand += pipeline.pop(i, 0.0)                      # 1. receive
        start = on_hand

        position = on_hand + sum(pipeline.values())          # 2. review and order
        qty = max(0.0, order_up_to[o] - position)
        pipeline[i + lead_time] = pipeline.get(i + lead_time, 0.0) + qty

        dmd = float(demand[o])                               # 3. demand
        sold = min(on_hand, dmd)
        unmet = dmd - sold
        on_hand -= sold

        if i >= warmup:
            scored += 1
            demand_total += dmd
            unmet_total += unmet
            stockout_weeks += unmet > 1e-6
            inventory.append((start + on_hand) / 2)

    return pd.Series(
        {
            "safety_stock": safety_stock,
            "CSL": 1 - stockout_weeks / scored,
            "fill_rate": 1 - unmet_total / demand_total,
            "avg_inventory": float(np.mean(inventory)),
            "weeks_scored": scored,
        }
    )


def build_frontier(
    bt: pd.DataFrame,
    cum: pd.DataFrame,
    lead_time: int,
    carrying_rate: float,
    grid: np.ndarray | None = None,
    warmup: int = 10,
) -> pd.DataFrame:
    """
    Sweep safety stock and record the service level actually delivered alongside
    the cost of delivering it.

    Comparing two models at different achieved service levels is meaningless, so
    the comparison must be read horizontally: at a fixed service level, the
    vertical gap between two curves is what the better forecast is worth.
    """
    grid = np.arange(0.0, 3.01, 0.1) if grid is None else grid
    rows = []

    for (store, model), g in cum.groupby(["store", "model"]):
        sigma = g["error_P"].std()
        for k in grid:
            r = simulate_policy(bt, store, model, k * sigma, lead_time, warmup)
            r["store"], r["model"], r["k"] = store, model, k
            rows.append(r)

    out = pd.DataFrame(rows)
    out["annual_cost"] = out["avg_inventory"] * carrying_rate
    return out


def cost_at_service(
    frontier: pd.DataFrame,
    store,
    model: str,
    metric: str,
    target: float,
) -> float:
    """
    Cheapest configuration that reaches the target on the given service metric.

    `metric` is "CSL" (probability a cycle avoids a stockout) or "fill_rate"
    (share of demand met). The two do not rank models identically: a forecast can
    stock out less often but more deeply, winning on the counting metric and
    losing on the depth metric.
    """
    sub = frontier[(frontier["store"] == store) & (frontier["model"] == model)]
    feasible = sub[sub[metric] >= target]
    return float(feasible["annual_cost"].min()) if len(feasible) else float("nan")
