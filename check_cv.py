"""
Quick check: compute the coefficient of variation (CV) of weekly sales
for each selected store, straight from your real train.csv.

CV = std / mean. A low CV means stable demand; a high CV means volatile demand.
Run from the project root with the venv active:

    python check_cv.py
"""

from src.data_loader import build_weekly_dataset

weekly = build_weekly_dataset()

print("Weekly sales — coefficient of variation by store\n")
for store, g in weekly.groupby("Store"):
    mean = g["Sales"].mean()
    std = g["Sales"].std()
    cv = std / mean
    label = "stable" if cv < 0.30 else "volatile"
    print(f"  Store {store}:  weeks={len(g):3d}  mean={mean:12,.0f}  "
          f"std={std:11,.0f}  CV={cv:.3f}  ({label})")
