# Forecast-Driven Inventory Control

## The question

Demand forecasting projects are almost always evaluated on forecast accuracy.
But accuracy is not the objective — inventory performance is. This project asks
a narrower and more useful question:

> Does choosing a forecasting model by accuracy actually produce the best
> inventory outcome?

To answer it, forecast error is not reported as MAPE. It is converted into the
quantity it actually drives — safety stock — and then priced in euros.

## Data

Rossmann Store Sales (Kaggle), 1,115 German drugstores, Jan 2013 – Jul 2015.
Two contrasting stores are analysed in depth:

| Store | Weekly mean | CV   | Profile          |
|-------|-------------|------|------------------|
| 733   | €104,201    | 0.09 | High, stable     |
| 198   | €16,802     | 0.36 | Low, volatile    |

The contrast is deliberate: inventory policy that works for a stable store
often fails for a volatile one, and aggregate metrics hide this.

## Key assumptions

Rossmann records turnover, not quantities, and contains no supply-side data.
Assumptions are therefore explicit and treated as parameters, not facts:

| Parameter | Value | Basis |
|-----------|-------|-------|
| Review period R | 1 week | Matches data granularity |
| Lead time L | 2 weeks | Assumed regional DC-to-store; stress-tested at 1, 2, 4 |
| Carrying rate | 20% / year | Standard retail range |
| Gross margin | 25% | Drugstore retail benchmark |

All costs are expressed as rates on inventory *value*, avoiding an invented
unit price.

## Findings
### Forecast accuracy ranks the two stores in the wrong order

Backtested with a rolling origin (53 replenishment decisions per store,
seasonal naive baseline, protection period P = 3 weeks):

| Store | Weekly MAPE | Safety stock as % of P-demand | Error autocorrelation |
|-------|-------------|-------------------------------|-----------------------|
| 198   | 23.9%       | 8.9%                          | 0.57                  |
| 733   | 7.1%        | 18.3%                         | 1.13                  |

Store 198 is 3.3x worse on MAPE yet requires less than half the safety stock
in relative terms. The reason is that MAPE scores each week independently,
while inventory is exposed to *cumulative* error across the protection period,
and the two stores' errors aggregate differently.

Store 198's forecast errors cancel: its promotion cycle alternates weekly, so
any three-week window contains roughly 1.5 cycles and over- and under-forecasts
offset. Its cumulative error is 57% of what the independence assumption
predicts. Store 733's errors persist — the store is growing, so a seasonal
baseline under-forecasts consistently — and its cumulative error is 113% of the
predicted value.

The textbook formula SS = z·σ·√L assumes independence and is wrong in both
directions:

| Store | Textbook SS | Empirical SS | Error | Annual carrying cost of the error |
|-------|-------------|--------------|-------|-----------------------------------|
| 198   | €16,298     | €9,252       | +€7,046 overstock  | €1,409               |
| 733   | €25,296     | €28,578      | −€3,283 understock | €657                 |

Store 733 additionally carries an uncorrected forecast bias of €10,110 over the
protection period, costing €2,022 per year — the cheapest available saving in
the project, since bias is a constant and can be removed by subtracting the
historical mean error.

These figures cover two stores selected for contrast, not a representative
sample, and should not be extrapolated linearly to the 1,115-store network.
## Findings

### The two stores serve different customers, and it shows in the data

Daily sales profiles identify what each store is, without any external
information:

| Day       | Store 733 | Store 198 |
|-----------|-----------|-----------|
| Mon–Fri   | ~15,000   | 2,700–4,200 |
| Saturday  | 14,015    | 936       |
| Sunday    | 15,144    | closed    |

Store 733 trades every day of the week at an almost flat rate, Sundays
included — the signature of a transit location (station or airport concourse)
serving a passing flow rather than a resident catchment. Store 198 peaks on
Monday, declines through the week and collapses on Saturday to a quarter of a
weekday, indicating a commuter catchment that empties at the weekend.

### Promotion, not uncertainty, drives most of the observed volatility

Both stores run the same chain-wide promotion calendar (Mon–Fri, 71 of 133
weeks). Their responses differ by an order of magnitude:

| Store | Non-promo week | Promo week | Uplift | Variance explained by promotion | CV total → residual |
|-------|----------------|------------|--------|--------------------------------|---------------------|
| 198   | €10,884        | €22,062    | +103%  | 84.2%                          | 0.362 → 0.144       |
| 733   | €100,448       | €108,365   | +8%    | 18.9%                          | 0.087 → 0.078       |

This reframes the problem. Promotions are scheduled by the retailer and known
weeks ahead, so the variance they explain is anticipated variation, not
uncertainty. Safety stock exists to absorb what cannot be anticipated. Store
198 is therefore not the volatile store it appears to be: its genuine demand
uncertainty is CV 0.144, not 0.362.

The practical implication is that forecasting investment does not pay off
evenly across a store network. It is tested in notebook 02.
### The accuracy gain and the inventory gain point at different stores

A promo-aware conditional mean — the mean of recent promotion weeks and the
mean of recent non-promotion weeks, selected by the published plan — replaces
the seasonal naive baseline. No machine learning is involved, so any gain is
attributable to the information rather than to model complexity.

| Store | MAE improvement | Inventory reduction | Annual saving |
|-------|-----------------|---------------------|---------------|
| 198   | −62%            | −8%                 | €160          |
| 733   | −14%            | −28%                | €2,175        |

The store with the larger accuracy gain delivers 13x less value. Ranking stores
by forecast accuracy would direct investment to the wrong one.

The mechanism is visible in the error autocorrelation factor — the ratio of
observed cumulative error to what independent weekly errors would produce:

| Store | Model | Autocorrelation | Bias stock | Safety stock |
|-------|-------|-----------------|------------|--------------|
| 198   | seasonal naive | 0.60 | €259    | €9,252  |
| 198   | promo-aware    | 1.40 | €29     | €8,684  |
| 733   | seasonal naive | 1.10 | €10,110 | €28,578 |
| 733   | promo-aware    | 1.10 | €1,361  | €26,453 |

Store 198's baseline errors alternate with the promotion cycle: it over-forecasts
in one week and under-forecasts in the next, and the two offset within any
three-week protection period (factor 0.60). The promo-aware model removes those
errors — and removes the cancellation with them (factor 1.40). Weekly error falls
62% while cumulative error falls 6%. The protection period was already absorbing
most of the problem for free.

Store 733's saving comes almost entirely from bias, which accumulates linearly
across the protection period and never cancels. Its bias stock falls from €10,110
to €1,361 — 93% of the total saving in this project — and the cause is not the
promotion information but the shorter estimation window, which tracks the store's
growth where a 52-week lookback lags it.

**Implication.** Forecast investment should be prioritised by error bias and error
autocorrelation, not by MAPE. A noisy but unbiased forecast on a short protection
period may need no improvement at all.
### The comparison reverses depending on how service level is defined

Sweeping safety stock on a fine grid and matching the two models at identical
achieved service produces opposite conclusions under the two standard service
definitions:

| Store | Target | Baseline | Promo-aware | Saving |
|-------|--------|----------|-------------|--------|
| 198 | 95% cycle service | €3,471 | €3,323 | **+€148** |
| 198 | 99% fill rate     | €3,141 | €4,119 | **−€978** |
| 733 | 95% cycle service | €15,749 | €15,058 | **+€691** |
| 733 | 98% cycle service | €16,077 | €19,304 | **−€3,226** |

Cycle service counts whether a stockout occurred; fill rate measures how much
demand went unmet. The promo-aware model stocks out less often but more deeply:
it compresses the centre of the error distribution without compressing the tail,
consistent with its error autocorrelation rising from 0.60 to 1.40. On a
counting metric it wins; on a depth metric it loses.

The consequence is organisational rather than technical. An operations team
tracking cycle service and a commercial team committed to a fill-rate SLA would
reach opposite investment decisions from the same data, and each would be
correct on its own metric.

**Conclusion.** Whether a better forecast is worth funding cannot be answered
until the service definition is fixed. In this dataset the choice of service
definition moves the answer by more than the choice of forecasting model does.

A related finding: at store 198, a configuration delivering 98% fill rate costs
€2,786/year against €3,471 for one targeting 95% cycle service. A retailer whose
true requirement is fill rate but whose policy is parameterised
### Every conclusion above depends on an unobservable parameter

Lead time is not in the dataset; L = 2 weeks was assumed at the outset. Re-running
the full pipeline at L = 1, 2 and 4 shows the assumption is not innocuous.

Annual saving from the promo-aware model at 95% cycle service:

| Store | P = 2 (1.0 promo cycles) | P = 3 (1.5) | P = 5 (2.5) |
|-------|--------------------------|-------------|-------------|
| 198   | +€343                    | +€98        | **−€574**   |
| 733   | **−€1,675**              | +€539       | **−€2,529** |

The sign reverses at both stores. The conclusion reached under L = 2 — that the
promo-aware model is worth funding — is an artefact of that specific assumption.

Part of the mechanism is a parity effect. Store 198's promotion calendar
alternates weekly, so the protection period spans 1.0, 1.5 or 2.5 promotion
cycles depending on lead time. Its baseline error autocorrelation tracks this
non-monotonically (0.41, 0.57, 0.44): cancellation is most complete when the
protection period covers a whole number of cycles. Store 733, where promotion
explains only 19% of variance, shows no such oscillation and rises monotonically
(1.01, 1.13, 1.22).

**Overall conclusion.** Three choices move the answer more than the choice of
forecasting model does: the metric used to evaluate forecasts, the definition of
service level, and the assumed lead time. Two are decisions the organisation can
make deliberately; the third is a fact it should measure. A forecasting
investment case built without settling all three is not evaluable, however
carefully the models themselves are benchmarked.

### Hypotheses tested and rejected

**Trading-day noise inflates store 198's volatility.** Rejected. Normalising
weekly sales by the number of trading days reduced CV by only 3.5% (0.362 →
0.349). 110 of 133 weeks have exactly six trading days, so dividing by a
near-constant leaves the coefficient of variation almost unchanged.

**Store 198's weak Saturdays are a data artefact.** Rejected. No open day
records zero sales at either store. Saturday sales are consistently low
(median €866, sd €327) and reflect genuine catchment behaviour.

## Repository structure

_To be completed._

## Reproducing

_To be completed._