# Databricks notebook source
# MAGIC %md
# MAGIC # 01 Setup
# MAGIC
# MAGIC Creates the schema and every table, loads stores and products, and seeds planning settings and the first admin.
# MAGIC Safe to re-run: it never overwrites settings you have edited.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

import pandas as pd

from stormsense_core import dbx, reference
from stormsense_core.tables import TABLES, create_sql

ctx = dbx.Ctx(spark, dbutils)
dbutils.widgets.text("admin_email", "", "Admin email (blank = the user running this notebook)")
admin_email = dbutils.widgets.get("admin_email").strip() or spark.sql("SELECT current_user()").first()[0]

# COMMAND ----------

spark.sql(f"CREATE SCHEMA IF NOT EXISTS `{ctx.catalog}`.`{ctx.schema}` COMMENT 'StormSense: weather-aware demand forecasts and store transfers'")
for name, table in TABLES.items():
    spark.sql(create_sql(ctx.fq(name), table))
print(f"Schema {ctx.catalog}.{ctx.schema} ready with {len(TABLES)} tables")

# COMMAND ----------

ctx.write(reference.stores_df(), "stores")
ctx.write(reference.products_df(), "products")

# Settings: add missing keys only, so edits made later survive a re-run.
ctx.frame(reference.settings_df(), "settings").createOrReplaceTempView("seed_settings")
spark.sql(f"""
    MERGE INTO {ctx.fq("settings")} t USING seed_settings s ON t.key = s.key
    WHEN NOT MATCHED THEN INSERT *
""")

# First admin: the person deploying. Add planners and viewers with plain INSERTs into app_users.
admin = pd.DataFrame([{"email": admin_email, "display_name": admin_email.split("@")[0].replace(".", " ").title(), "role": "admin"}])
ctx.frame(admin, "app_users").createOrReplaceTempView("seed_admin")
spark.sql(f"MERGE INTO {ctx.fq('app_users')} t USING seed_admin s ON lower(t.email) = lower(s.email) WHEN NOT MATCHED THEN INSERT *")
display(spark.table(ctx.fq("settings")))
