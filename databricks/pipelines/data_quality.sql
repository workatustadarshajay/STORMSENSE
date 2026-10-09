-- Lakeflow Declarative Pipeline: data-quality gates in front of the forecast.
-- Rows that break a rule are dropped and counted in the pipeline's quality metrics.
-- A weather reading that cannot be physically right stops the run, so no forecast is built on it.
-- Downstream steps read these *_clean views, not the raw tables.

CREATE OR REFRESH MATERIALIZED VIEW sales_clean (
  CONSTRAINT units_not_negative EXPECT (units >= 0) ON VIOLATION DROP ROW,
  CONSTRAINT sale_date_present EXPECT (sale_date IS NOT NULL) ON VIOLATION DROP ROW,
  CONSTRAINT store_present EXPECT (store_id IS NOT NULL)
)
COMMENT 'Daily units sold per store and product, with rows that break basic rules removed'
AS SELECT store_id, product_id, sale_date, units, revenue_usd FROM sales_history;

CREATE OR REFRESH MATERIALIZED VIEW weather_observed_clean (
  CONSTRAINT plausible_temperature EXPECT (temp_max_f BETWEEN -40 AND 135) ON VIOLATION FAIL UPDATE,
  CONSTRAINT rain_not_negative EXPECT (rain_in >= 0) ON VIOLATION DROP ROW,
  CONSTRAINT wind_not_negative EXPECT (wind_max_mph >= 0) ON VIOLATION DROP ROW
)
COMMENT 'Observed daily weather per store; an implausible temperature stops the run'
AS SELECT store_id, obs_date, temp_max_f, temp_min_f, rain_in, wind_max_mph, condition, event_name FROM weather_observed;

CREATE OR REFRESH MATERIALIZED VIEW inventory_clean (
  CONSTRAINT on_hand_not_negative EXPECT (on_hand >= 0) ON VIOLATION DROP ROW,
  CONSTRAINT in_transit_not_negative EXPECT (in_transit >= 0) ON VIOLATION DROP ROW,
  CONSTRAINT snapshot_date_present EXPECT (snapshot_date IS NOT NULL) ON VIOLATION DROP ROW
)
COMMENT 'End-of-day stock per store and product, with impossible counts removed'
AS SELECT store_id, product_id, snapshot_date, on_hand, in_transit FROM inventory_snapshot;
