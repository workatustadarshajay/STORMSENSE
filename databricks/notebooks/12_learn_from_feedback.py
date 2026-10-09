# Databricks notebook source
# MAGIC %md
# MAGIC # 12 Learn from planner decisions
# MAGIC
# MAGIC Turns recent rejections into `route_preferences`. A route rejected lately ranks lower in the next recommendations, and
# MAGIC older rejections fade over 60 days. Overwrites the table on each run, so it is safe to repeat.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

from datetime import datetime, timezone

import pandas as pd

from stormsense_core import dbx
from stormsense_core.feedback import COLUMNS, compute_route_preferences

ctx = dbx.Ctx(spark, dbutils)
as_of = ctx.as_of()

# COMMAND ----------

rej = spark.sql(f"SELECT rec_id, source_store_id, dest_store_id, product_id, reason_code, decided_at FROM {ctx.fq('rejection_feedback')}").toPandas()
prefs = compute_route_preferences(rej, as_of, now=datetime.now(timezone.utc).replace(tzinfo=None))
if prefs.empty:
    prefs = pd.DataFrame(columns=COLUMNS)
n = ctx.write(prefs, "route_preferences")
print(f"route_preferences: {n} learned routes from {len(rej)} rejections")
display(spark.table(ctx.fq("route_preferences")))
