# Forecasting method

## What is forecast

Units sold per store, product and day, for the 7 days after the latest stock count. One forecaster serves every store and product (store and product are categorical features).

## Features (one row per store, product and date)

| Group | Features |
|---|---|
| Calendar | day of week, month, weekend, US federal holiday |
| Weather on the day | highest temperature, rainfall, strongest gust |
| Weather ahead | strongest wind over the next two days, rain over the next three, temperature change over two days |
| Sales history | sales exactly 7 days earlier, 7-day and 28-day averages ending 7 days earlier |

Weather ahead matters because demand for generators, plywood, tarps and pumps rises one to two days **before** a storm arrives.

## How leakage is avoided

1. **Sales features are lagged by the forecast horizon (7 days).** A row for date *d* only sees sales up to *d - 7*. The same row can therefore be built today for any of the next 7 days, and for any day in the past, with identical meaning. The target (units sold on *d*) appears in no feature of any row. A test checks the lag against the raw sales.
2. **Weather is forecast-time information.** For future days it comes from the provider's forecast. For history we only have observed weather, so training and validation add forecast-sized error (growing with lead time) to it. Without this the model would learn from a perfect forecast and look better than it is in use.
3. **Time-based split.** Train on everything before the last four weeks; validate on those four weeks. Never a random split.

## Measuring honestly

* **WAPE** (total absolute error divided by total actual units) is the headline. MAPE is reported only as a secondary number because it is undefined at zero.
* Two baselines on the same four weeks: **same as last week** and **trailing 28-day average**.
* The forecaster is registered in Unity Catalog and given the alias `champion` **only if it beats both baselines**. Otherwise the task fails and the current champion stays. Everything downstream loads by alias, never by version number.
* Each training run is recorded in `model_runs` and in MLflow.

On the sample data, local training gives WAPE ≈ 0.40 against 0.67 (same as last week) and 0.57 (28-day average). Counts per store and day are small, so a sizeable share of the error is irreducible noise.

## Uncertainty and confidence

For each product, take every rolling 7-day window in the validation period, per store, and compare actual weekly demand with forecast weekly demand. The 10th and 90th percentiles of that ratio (`forecast_intervals`) give a low case and a high case for the week.

A transfer's **confidence** is the share of the move that is still needed in the low-demand case: `shortfall at the 10th percentile / shortfall at the forecast`. At 0.7 or more it reads High, at 0.4 or more Medium, otherwise Low. Nothing is hardcoded per transfer.

## Shortage, surplus and transfers

Settings live in the `settings` table (safety stock 2 days, surplus at 21 days of cover, urgent within 2 days or $5,000 of lost sales, 300 miles maximum, 10 units minimum, 7-day horizon).

* **Projected stock** = on hand + on the way + approved arrivals - approved departures - cumulative forecast.
* **SHORTAGE:** projected stock falls below the safety level within the week.
* **SURPLUS:** at least the surplus threshold of days of cover **and** units left after protecting its own forecast and safety stock.
* **Matching:** per product, the shortage with the most sales at risk is served first, nearest source first, within the distance limit, in whole packs, never more than a source can spare.
* **URGENT:** the store runs out within the urgent window, or the lost sales value is high.
* **Sales protected** = units that would have gone unsold, valued at the product price.
