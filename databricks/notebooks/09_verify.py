# Databricks notebook source
# MAGIC %md
# MAGIC # 09 Verification
# MAGIC
# MAGIC Fails loudly if anything is off. `build` adds the checks that guarantee a meaningful first run (weather really drives demand, both
# MAGIC shortage and surplus exist, at least five pending transfers). `daily` checks freshness and integrity only, because planners
# MAGIC legitimately clear pending transfers.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

import mlflow
from mlflow.tracking import MlflowClient

from stormsense_core import dbx

ctx = dbx.Ctx(spark, dbutils)
dbutils.widgets.dropdown("mode", "daily", ["build", "daily"], "Checks")
mode = dbutils.widgets.get("mode")
as_of = ctx.as_of()
mlflow.set_registry_uri("databricks-uc")
failures: list[str] = []


def check(ok: bool, message: str) -> None:
    print(("PASS  " if ok else "FAIL  ") + message)
    if not ok:
        failures.append(message)


def q(sql: str):
    return spark.sql(sql).first()[0]


def avg_units(product: str, condition: str) -> float:
    return q(f"""SELECT avg(units) FROM {ctx.fq('sales_history')} s JOIN {ctx.fq('weather_observed')} w
                 ON s.store_id = w.store_id AND s.sale_date = w.obs_date
                 WHERE s.product_id = '{product}' AND w.condition = '{condition}'""")

# COMMAND ----------

# Tables exist and are filled.
for name in ("stores", "products", "settings", "weather_observed", "weather_forecast", "sales_history", "inventory_snapshot",
             "features", "predictions", "inventory_gaps"):
    check(q(f"SELECT count(*) FROM {ctx.fq(name)}") > 0, f"{name} has rows")
check(q(f"SELECT count(*) FROM {ctx.fq('stores')}") == 10 and q(f"SELECT count(*) FROM {ctx.fq('products')}") == 5, "10 stores and 5 products")

# Dates line up.
check(q(f"SELECT datediff(max(sale_date), min(sale_date)) FROM {ctx.fq('sales_history')}") >= 360, "sales cover about a year")
check(q(f"SELECT max(snapshot_date) FROM {ctx.fq('inventory_snapshot')}") == as_of, f"stock snapshot is for {as_of}")
check(q(f"SELECT count(DISTINCT forecast_date) FROM {ctx.fq('weather_forecast')} WHERE forecast_date > '{as_of}'") >= 7, "7+ days of weather ahead")
check(q(f"SELECT count(*) FROM {ctx.fq('predictions')} WHERE as_of_date = '{as_of}'") == 350, "350 forecasts: 10 stores x 5 products x 7 days")
check(q(f"SELECT count(*) FROM {ctx.fq('predictions')} WHERE predicted_units < 0 OR predicted_units IS NULL") == 0, "no negative or missing forecasts")

# The forecaster is the champion and was measured honestly.
mv = MlflowClient().get_model_version_by_alias(f"{ctx.catalog}.{ctx.schema}.demand_forecaster", "champion")
check(q(f"SELECT count(*) FROM {ctx.fq('predictions')} WHERE as_of_date = '{as_of}' AND model_version = '{mv.version}'") == 350, f"forecasts come from champion version {mv.version}")
run = spark.sql(f"SELECT * FROM {ctx.fq('model_runs')} WHERE model_version = '{mv.version}'").first()
check(run is not None and run.wape_model < run.wape_same_as_last_week and run.wape_model < run.wape_trailing_28d_avg, "forecaster beats both baselines on the last four weeks")

# Recommendations obey the rules.
check(q(f"""SELECT count(*) FROM (SELECT 1 FROM {ctx.fq('transfer_recommendations')} WHERE status = 'PENDING'
            GROUP BY as_of_date, source_store_id, dest_store_id, product_id HAVING count(*) > 1)""") == 0, "no duplicate pending transfers")
check(q(f"SELECT count(*) FROM {ctx.fq('transfer_recommendations')} t JOIN {ctx.fq('settings')} s ON s.key = 'min_transfer_qty' WHERE t.status = 'PENDING' AND t.qty < CAST(s.value AS DOUBLE)") == 0, "pending transfers meet the minimum quantity")

# COMMAND ----------

if mode == "build":
    # Weather must really drive demand: generators sell far more on storm days, coolers more on hot days.
    check(avg_units("P01", "storm") > 3 * avg_units("P01", "clear"), "generators sell 3x+ more on storm days")
    check(avg_units("P05", "heat") > 1.3 * avg_units("P05", "clear"), "coolers sell 1.3x+ more on hot days")
    check(q(f"SELECT count(DISTINCT event_name) FROM {ctx.fq('weather_observed')}") >= 4, "4+ named events in the history")
    status = {r.status for r in spark.sql(f"SELECT DISTINCT status FROM {ctx.fq('inventory_gaps')} WHERE as_of_date = '{as_of}'").collect()}
    check({"SHORTAGE", "SURPLUS"} <= status, "the latest stock has both shortage and surplus")
    check(q(f"SELECT count(*) FROM {ctx.fq('transfer_recommendations')} WHERE status = 'PENDING'") >= 5, "at least 5 pending transfers")

if failures:
    raise AssertionError(f"{len(failures)} check(s) failed:\n- " + "\n- ".join(failures))
print(f"All checks passed ({mode}).")
