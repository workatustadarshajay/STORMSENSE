# Databricks notebook source
# MAGIC %md
# MAGIC # 07 Shortage and surplus
# MAGIC
# MAGIC Projects stock over the 7 days (on hand plus on the way, minus forecast demand) and classifies each store and product as
# MAGIC SHORTAGE, SURPLUS or BALANCED using the thresholds in `settings`. Approved transfers count as stock arriving or leaving.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

import pandas as pd

from stormsense_core import dbx, planning

ctx = dbx.Ctx(spark, dbutils)
as_of = ctx.as_of()

# COMMAND ----------

preds = ctx.read("predictions")
preds = preds[pd.to_datetime(preds["as_of_date"]).dt.date == as_of]
inv = ctx.read("inventory_clean")
inv = inv[pd.to_datetime(inv["snapshot_date"]).dt.date == as_of]
version = preds["model_version"].iloc[0]
intervals = ctx.read("forecast_intervals").query("model_version == @version")

gaps = planning.compute_gaps(preds, inv, planning.committed_from_recs(ctx.read("transfer_recommendations"), as_of),
                             intervals, ctx.setting_values(), as_of)
n = ctx.write(gaps, "inventory_gaps", replace_where=f"as_of_date = '{as_of}'")
print(f"inventory_gaps: {n} rows;", gaps["status"].value_counts().to_dict())
