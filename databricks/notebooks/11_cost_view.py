# Databricks notebook source
# MAGIC %md
# MAGIC # 11 Cost view
# MAGIC
# MAGIC Creates `cost_daily`: StormSense's Databricks usage per day and SKU, from billing system tables.
# MAGIC Only usage from jobs tagged `project: stormsense` is included. Dollar figures are estimates at list price;
# MAGIC they stay blank when the list price for a SKU is not published in this region.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

from stormsense_core import dbx

ctx = dbx.Ctx(spark, dbutils)

# COMMAND ----------

spark.sql(f"""
CREATE OR REPLACE VIEW {ctx.fq('cost_daily')}
COMMENT 'StormSense Databricks usage per day and SKU, from billing system tables (jobs tagged project=stormsense)'
AS
SELECT u.usage_date, u.sku_name, sum(u.usage_quantity) AS dbus, round(sum(u.usage_quantity * p.price), 2) AS est_usd
FROM system.billing.usage u
LEFT JOIN (
  SELECT sku_name, max(pricing.default) AS price
  FROM system.billing.list_prices
  WHERE price_end_time IS NULL
  GROUP BY sku_name
) p ON p.sku_name = u.sku_name
WHERE u.custom_tags['project'] = 'stormsense'
GROUP BY u.usage_date, u.sku_name
""")
display(spark.sql(f"SELECT count(*) AS days_with_usage, round(sum(dbus), 2) AS dbus FROM {ctx.fq('cost_daily')}"))
