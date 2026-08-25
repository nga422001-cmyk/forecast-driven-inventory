"""
Rolling-origin backtesting.

Random train/test splitting leaks future information into training and makes the
resulting score meaningless for a time series. A forecast must be evaluated the
way it is used: standing at week t, seeing only weeks 1..t, predicting t+1..t+H.
Each iteration here reproduces one replenishment decision.

The forecast horizon is not a free choice. Under periodic review (R, S) an order
placed now arrives after lead time L, but the *next* order only arrives at R + L,
so on-hand stock must cover demand over the protection period P = R + L. H = P.
"""

from __future__ import annotations

import numpy as np
import pandas as pd

from . import forecasting


def build_promo_plan(
    panel: pd.DataFrame,
    horizon: int,
    store_col: str = "Store",
    date_col: str = "WeekEnding",
    promo_col: str = "PromoShare",
) -> pd.DataFrame:
    """
    Materialise the promotion calendar as a standalone artefact.

    Numerically identical to reading the column from the sales panel; the
    separation is what makes it auditable that a model reads a published plan
    rather than the realised future. `known_at` states the assumption explicitly:
    the calendar is fixed at least one protection period ahead.
    """
    plan = panel[[store_col, date_col, promo_col]].copy()
    plan["known_at"] = plan[date_col] - pd.Timedelta(weeks=horizon)
    plan["is_promo"] = plan[promo_col] > 0
    return plan.set_index([store_col, date_col])


def run_backtest(
    panel: pd.DataFrame,
    promo_plan: pd.DataFrame,
    horizon: int,
    min_train: int,
    models: dict | None = None,
    season: int = 52,
    store_col: str = "Store",
    date_col: str = "WeekEnding",
    target_col: str = "Sales",
) -> pd.DataFrame:
    """
    Walk-forward evaluation over every origin with enough history.

    Returns one row per (store, model, origin, h):
        store | model | origin | target_date | h | y_true | y_pred | promo | error
    """
    models = models or forecasting.MODELS
    rows = []

    for store, g in panel.groupby(store_col):
        g = g.sort_values(date_col).set_index(date_col)
        s = g[target_col].astype(float)
        plan = promo_plan.loc[store, "is_promo"]

        for t in range(min_train, len(s) - horizon + 1):
            history = s.iloc[:t]
            hist_promo = plan.iloc[:t]
            actual = s.iloc[t : t + horizon]
            future_promo = plan.iloc[t : t + horizon]

            for name, fn in models.items():
                yhat = np.asarray(
                    fn(
                        history,
                        horizon,
                        hist_promo=hist_promo,
                        future_promo=future_promo,
                        season=season,
                    ),
                    dtype=float,
                )
                if len(yhat) != horizon or not np.all(np.isfinite(yhat)):
                    continue

                for i in range(horizon):
                    rows.append(
                        {
                            "store": store,
                            "model": name,
                            "origin": s.index[t - 1],
                            "target_date": actual.index[i],
                            "h": i + 1,
                            "y_true": actual.iloc[i],
                            "y_pred": yhat[i],
                            "promo": bool(future_promo.iloc[i]),
                        }
                    )

    bt = pd.DataFrame(rows)
    bt["error"] = bt["y_pred"] - bt["y_true"]  # positive = over-forecast
    return bt


def drop_boundary_weeks(
    panel: pd.DataFrame,
    store_col: str = "Store",
    date_col: str = "WeekEnding",
) -> pd.DataFrame:
    """
    Remove the first and last week of each store's series.

    These are truncated by the dataset boundary rather than by trading behaviour
    (the Rossmann panel starts on a Tuesday and ends on a Thursday), so their
    totals reflect missing days and would otherwise be read as demand drops.
    """
    bounds = panel.groupby(store_col)[date_col].agg(["min", "max"])
    keep = panel.apply(
        lambda r: r[date_col] not in (
            bounds.loc[r[store_col], "min"],
            bounds.loc[r[store_col], "max"],
        ),
        axis=1,
    )
    return panel[keep].copy()


def accuracy_table(bt: pd.DataFrame, by_horizon: bool = False) -> pd.DataFrame:
    """RMSE / MAE / MAPE / bias per store x model, optionally split by horizon."""
    keys = ["store", "model"] + (["h"] if by_horizon else [])

    def _agg(g):
        return pd.Series(
            {
                "n": len(g),
                "RMSE": np.sqrt((g["error"] ** 2).mean()),
                "MAE": g["error"].abs().mean(),
                "MAPE_%": (g["error"].abs() / g["y_true"]).mean() * 100,
                "bias_%": g["error"].mean() / g["y_true"].mean() * 100,
            }
        )

    return bt.groupby(keys).apply(_agg, include_groups=False).reset_index()
