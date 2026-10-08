# Databricks notebook source
# MAGIC %md
# MAGIC # 02 Sample data
# MAGIC
# MAGIC Generates a year of sample weather, sales and stock ending yesterday, plus a ten-day weather forecast that includes a storm
# MAGIC and a heat wave. Demand is driven by the weather, so the forecaster has real signal to learn. Seeded, so it is reproducible.
# MAGIC Replaces the four feed tables; recommendations and decisions are not touched.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

from datetime import date, timedelta

from stormsense_core import dbx, synth

ctx = dbx.Ctx(spark, dbutils)
dbutils.widgets.text("end_date", "", "Last day of history (blank = yesterday)")
end = date.fromisoformat(dbutils.widgets.get("end_date").strip()) if dbutils.widgets.get("end_date").strip() else date.today() - timedelta(days=1)

# COMMAND ----------

data = synth.generate(end)
for name, pdf in data.tables.items():
    print(f"{name}: {ctx.write(pdf, name):,} rows")

# COMMAND ----------

display(spark.sql(f"""
    SELECT 'sales_history' AS table, min(sale_date) AS first_day, max(sale_date) AS last_day, count(*) AS rows FROM {ctx.fq("sales_history")}
    UNION ALL SELECT 'weather_observed', min(obs_date), max(obs_date), count(*) FROM {ctx.fq("weather_observed")}
    UNION ALL SELECT 'weather_forecast', min(forecast_date), max(forecast_date), count(*) FROM {ctx.fq("weather_forecast")}
    UNION ALL SELECT 'inventory_snapshot', min(snapshot_date), max(snapshot_date), count(*) FROM {ctx.fq("inventory_snapshot")}
"""))
