# Databricks notebook source
# MAGIC %md
# MAGIC # 14 Backtest past storms
# MAGIC
# MAGIC Replays each named storm in the history with what really sold. For every store and product it finds the stock on
# MAGIC hand when the storm started, the units sold beyond it (lost sales), and how much a nearby store with spare stock
# MAGIC could have covered. Results go to `backtest_results`. This is an upper bound: it uses actual demand, not forecasts.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

from stormsense_core import backtest, dbx

ctx = dbx.Ctx(spark, dbutils)

# COMMAND ----------

observed = spark.table(ctx.fq("weather_observed")).toPandas()
sales = spark.table(ctx.fq("sales_history")).toPandas()
inventory = spark.table(ctx.fq("inventory_snapshot")).toPandas()
products = spark.table(ctx.fq("products")).toPandas()
stores = spark.table(ctx.fq("stores")).toPandas()

results = backtest.replay_all(observed, sales, inventory, products, stores)
ctx.write(results, "backtest_results", new_schema=True)
print(results.to_string())
