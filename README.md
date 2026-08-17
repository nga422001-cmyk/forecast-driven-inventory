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

_To be completed._

## Repository structure

_To be completed._

## Reproducing

_To be completed._