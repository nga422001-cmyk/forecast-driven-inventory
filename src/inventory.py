"""
Safety stock sizing from the empirical distribution of cumulative forecast error.

Safety stock does not absorb weekly forecast error; it absorbs the error of
cumulative demand over the protection period. The two aggregate differently:
independent noise grows with sqrt(P), while bias grows linearly with P. A model
that is noisy but unbiased can therefore need less safety stock than one that
looks more accurate week by week but drifts in one direction.

The textbook formula SS = z * sigma_weekly * sqrt(L) assumes weekly errors are
independent. Where they are not — a promotion calendar that makes errors
alternate and cancel, or a growth trend that makes them persist — the formula is
wrong, and the direction of the error depends on the sign of the autocorrelation.
"""

from __future__ import annotations

from statistics import NormalDist

import numpy as np
import pandas as pd


def z_score(service_level: float) -> float:
    """Inverse normal CDF. Kept here so the normal assumption is visible."""
    return NormalDist().inv_cdf(service_level)


def protection_period_errors(bt: pd.DataFrame, protection: int | None = None) -> pd.DataFrame:
    """
    Aggregate per-period errors into the error of cumulative demand over the
    protection period. One row per (store, model, origin).
    """
    df = bt if protection is None else bt[bt["h"] <= protection]
    out = (
        df.groupby(["store", "model", "origin"])
        .agg(
            forecast_P=("y_pred", "sum"),
            actual_P=("y_true", "sum"),
            periods=("h", "count"),
        )
        .reset_index()
    )
    out["error_P"] = out["forecast_P"] - out["actual_P"]
    return out


def decompose_error(bt: pd.DataFrame, cum: pd.DataFrame, horizon: int) -> pd.DataFrame:
    """
    Split cumulative forecast error into bias and dispersion, and measure how far
    the errors depart from independence.

    `autocorr_factor` is the ratio of observed cumulative error to what
    independent weekly errors would produce. Below 1 the errors cancel across the
    protection period; above 1 they persist and the textbook formula understocks.
    """
    weekly_std = bt.groupby(["store", "model"])["error"].std()

    res = cum.groupby(["store", "model"]).agg(
        mean_demand_P=("actual_P", "mean"),
        bias_P=("error_P", "mean"),
        std_P=("error_P", "std"),
        n_origins=("origin", "count"),
    )
    res["expected_if_independent"] = weekly_std * np.sqrt(horizon)
    res["autocorr_factor"] = res["std_P"] / res["expected_if_independent"]
    res["bias_%"] = res["bias_P"] / res["mean_demand_P"] * 100
    return res


def safety_stock(
    cum: pd.DataFrame,
    service_level: float,
    method: str = "empirical",
) -> pd.DataFrame:
    """
    Size safety stock per (store, model).

    method="normal"    : z * sigma of cumulative error. Assumes normality.
    method="empirical" : the service-level quantile of realised shortfall.
                         Makes no distributional assumption, which matters where
                         the error distribution is bimodal or skewed.

    Uncorrected bias is reported separately. Bias is not uncertainty and should be
    removed by correcting the forecast, not absorbed by holding extra stock.
    """
    z = z_score(service_level)
    rows = []

    for (store, model), g in cum.groupby(["store", "model"]):
        shortfall = -g["error_P"]  # positive = demand exceeded forecast
        sigma = g["error_P"].std()

        ss_normal = z * sigma
        ss_empirical = float(np.quantile(shortfall, service_level))
        ss = ss_normal if method == "normal" else ss_empirical

        rows.append(
            {
                "store": store,
                "model": model,
                "service_level": service_level,
                "ss_normal": ss_normal,
                "ss_empirical": ss_empirical,
                "safety_stock": ss,
                "bias_stock": max(0.0, -g["error_P"].mean()),
                "skew": shortfall.skew(),
                "kurtosis": shortfall.kurtosis(),
            }
        )

    return pd.DataFrame(rows).set_index(["store", "model"])
