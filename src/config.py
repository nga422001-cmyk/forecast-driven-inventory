"""
Central configuration for the Forecast-Driven Inventory Optimization project.

All tunable parameters live here so that scripts, notebooks, and the main
pipeline stay consistent. Changing an assumption (lead time, service target,
cost rate) should require editing only this file.
"""

from pathlib import Path

# --- Paths -----------------------------------------------------------------
# Resolve project root relative to this file (src/ -> project root).
ROOT = Path(__file__).resolve().parents[1]
DATA_RAW = ROOT / "data" / "raw"
DATA_PROCESSED = ROOT / "data" / "processed"
OUTPUTS_FIGURES = ROOT / "outputs" / "figures"
OUTPUTS_TABLES = ROOT / "outputs" / "tables"

# Raw data file name. Kept out of GitHub via .gitignore.
RAW_DATA_FILE = DATA_RAW / "train.csv"

# --- Store selection -------------------------------------------------------
# Two contrasting stores: one with stable demand, one with volatile demand.
# This lets the inventory model show how policy parameters react to variability.
STORE_STABLE = 733       # low coefficient of variation
STORE_VOLATILE = 198     # high coefficient of variation
SELECTED_STORES = [STORE_STABLE, STORE_VOLATILE]

# --- Forecasting -----------------------------------------------------------
# Fraction of the weekly series held out for validation / test.
TEST_SIZE_WEEKS = 12
SEASONAL_PERIOD = 52     # weekly data, yearly seasonality

# --- Inventory assumptions -------------------------------------------------
DEMAND_SCALE = "weekly"
LEAD_TIME_WEEKS = 1              # base-case deterministic lead time
REVIEW_PERIOD_WEEKS = 1         # R for the periodic (R,S) policy
TARGET_FILL_RATE = 0.95         # service-level constraint (beta)
SHORTAGE_ASSUMPTION = "lost_sales"

# --- Cost structure --------------------------------------------------------
# Unit cost normalized to 1, so total cost is a relative cost index.
UNIT_COST = 1.0
ANNUAL_HOLDING_RATE = 0.15                      # 15% of unit cost per year
WEEKLY_HOLDING_COST = UNIT_COST * ANNUAL_HOLDING_RATE / 52
ORDERING_COST = 20.0                            # fixed cost per order (K)
SHORTAGE_COST = 1.0                             # penalty per unit short (B)

# --- Simulation ------------------------------------------------------------
N_SIM_PATHS = 10_000            # Monte Carlo demand paths
RANDOM_SEED = 42                # reproducibility

# --- Reporting -------------------------------------------------------------
FIGURE_DPI = 150
# ---------------------------------------------------------------------------
# Inventory policy parameters
#
# The forecast horizon is not a free choice: it is dictated by the replenishment
# policy. Under periodic review (R, S), an order placed now arrives after lead
# time L, but the *next* order only arrives at R + L. On-hand stock must
# therefore cover demand over the protection period P = R + L.
#
# Assumptions (also documented in README.md):
#   R = 1 week  - Rossmann stores are assumed to replenish weekly, matching the
#                 weekly granularity of the aggregated dataset.
#   L = 2 weeks - Not available in the dataset. Chosen as a plausible regional
#                 DC-to-store lead time for European drugstore retail. Treated
#                 as a parameter, not a fact: notebook 05 stress-tests L in
#                 {1, 2, 4} to check whether conclusions are robust to it.
# ---------------------------------------------------------------------------

REVIEW_PERIOD = 1                              # R, weeks
LEAD_TIME = 2                                  # L, weeks
PROTECTION_PERIOD = REVIEW_PERIOD + LEAD_TIME  # P, weeks
HORIZON = PROTECTION_PERIOD                    # forecast horizon follows P

# Inventory economics. Rossmann `Sales` is turnover in EUR, not quantity, so all
# costs are expressed as rates on value rather than per-unit costs. This avoids
# inventing an unobserved unit price.
SERVICE_LEVEL = 0.95           # target cycle service level
CARRYING_RATE_ANNUAL = 0.20    # holding cost, share of inventory value per year
GROSS_MARGIN = 0.25            # margin lost per EUR of unmet demand

# Backtesting
MIN_TRAIN_WEEKS = 78           # 1.5 years, enough for a seasonal-naive lookback
SEASON_LENGTH = 52             # weekly data, yearly seasonality
# ---------------------------------------------------------------------------
# Inventory policy parameters
#
# The forecast horizon is not a free choice: it is dictated by the replenishment
# policy. Under periodic review (R, S), an order placed now arrives after lead
# time L, but the *next* order only arrives at R + L. On-hand stock must
# therefore cover demand over the protection period P = R + L.
#
# Assumptions (also documented in README.md):
#   R = 1 week  - Rossmann stores are assumed to replenish weekly, matching the
#                 weekly granularity of the aggregated dataset.
#   L = 2 weeks - Not available in the dataset. Chosen as a plausible regional
#                 DC-to-store lead time for European drugstore retail. Treated
#                 as a parameter, not a fact: notebook 05 stress-tests L in
#                 {1, 2, 4} to check whether conclusions are robust to it.
# ---------------------------------------------------------------------------

REVIEW_PERIOD = 1                              # R, weeks
LEAD_TIME = 2                                  # L, weeks
PROTECTION_PERIOD = REVIEW_PERIOD + LEAD_TIME  # P, weeks
HORIZON = PROTECTION_PERIOD                    # forecast horizon follows P

# Inventory economics. Rossmann `Sales` is turnover in EUR, not quantity, so all
# costs are expressed as rates on value rather than per-unit costs. This avoids
# inventing an unobserved unit price.
SERVICE_LEVEL = 0.95           # target cycle service level
CARRYING_RATE_ANNUAL = 0.20    # holding cost, share of inventory value per year
GROSS_MARGIN = 0.25            # margin lost per EUR of unmet demand

# Backtesting
MIN_TRAIN_WEEKS = 78           # 1.5 years, enough for a seasonal-naive lookback
SEASON_LENGTH = 52             # weekly data, yearly seasonality