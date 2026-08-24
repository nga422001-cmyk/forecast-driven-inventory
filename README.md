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