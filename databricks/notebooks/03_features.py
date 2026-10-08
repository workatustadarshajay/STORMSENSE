# Databricks notebook source
# MAGIC %md
# MAGIC # 03 Features
# MAGIC
# MAGIC One row per store, product and date: calendar, weather (including the next three days) and sales history.
# MAGIC Sales features are lagged by the 7-day horizon, so a row only uses what is known at prediction time. Rebuilt in full on each run.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

from stormsense_core import dbx, features

ctx = dbx.Ctx(spark, dbutils)
as_of = ctx.as_of()

# COMMAND ----------

feats = features.build_features(ctx.read("sales_history"), ctx.read("weather_observed"), ctx.read("weather_forecast"), as_of)
feats["date"] = feats["date"].dt.date
ctx.write(feats, "features", new_schema=True)
print(f"features: {len(feats):,} rows through {feats['date'].max()} ({int(feats['is_future'].sum())} future rows) as of {as_of}")
