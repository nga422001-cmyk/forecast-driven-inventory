"""
Data loading and weekly aggregation for the Rossmann Store Sales dataset.

Role:
  Read the raw daily sales file, filter to the selected stores, keep only open
  days with valid sales, and aggregate daily sales into a clean weekly series
  that the forecasting and inventory modules consume.

Expected raw columns (Rossmann `train.csv`):
  Store, DayOfWeek, Date, Sales, Customers, Open, Promo, StateHoliday, SchoolHoliday
"""

from __future__ import annotations

import pandas as pd

from src import config


def load_raw(path=None) -> pd.DataFrame:
    """Load the raw daily Rossmann file and parse dates.

    Args:
        path: Optional override for the raw data path. Defaults to config.RAW_DATA_FILE.

    Returns:
        Daily DataFrame with a parsed `Date` column, sorted by store and date.
    """
    path = path or config.RAW_DATA_FILE
    df = pd.read_csv(path, parse_dates=["Date"], low_memory=False)
    df = df.sort_values(["Store", "Date"]).reset_index(drop=True)
    return df


def filter_stores(df: pd.DataFrame, stores=None) -> pd.DataFrame:
    """Keep only the selected stores and days the store was actually open.

    Closed days (Open == 0) carry zero sales and would distort both the
    forecast and the demand-uncertainty estimates, so they are removed.
    """
    stores = stores or config.SELECTED_STORES
    df = df[df["Store"].isin(stores)].copy()
    df = df[df["Open"] == 1]
    df = df[df["Sales"] > 0]
    return df


def aggregate_weekly(df: pd.DataFrame) -> pd.DataFrame:
    """Aggregate daily sales into a weekly series per store.

    Weeks are anchored to Sunday week-ending ("W" resample). Promo intensity
    is kept as the share of promo days in the week, which is a useful weekly
    exogenous feature for forecasting.

    Returns:
        Weekly DataFrame with columns: Store, WeekEnding, Sales, PromoShare, OpenDays.
    """
    frames = []
    for store, g in df.groupby("Store"):
        g = g.set_index("Date").sort_index()
        weekly = g.resample("W").agg(
            Sales=("Sales", "sum"),
            PromoShare=("Promo", "mean"),
            OpenDays=("Open", "count"),
        )
        # Drop partial leading/trailing weeks with too few open days.
        weekly = weekly[weekly["OpenDays"] >= 4]
        weekly["Store"] = store
        weekly = weekly.reset_index().rename(columns={"Date": "WeekEnding"})
        frames.append(weekly)

    out = pd.concat(frames, ignore_index=True)
    return out[["Store", "WeekEnding", "Sales", "PromoShare", "OpenDays"]]


def build_weekly_dataset(path=None, stores=None) -> pd.DataFrame:
    """End-to-end helper: raw file -> filtered -> weekly series."""
    daily = load_raw(path)
    daily = filter_stores(daily, stores)
    weekly = aggregate_weekly(daily)
    return weekly


if __name__ == "__main__":
    weekly = build_weekly_dataset()
    print(weekly.groupby("Store")["Sales"].describe())
