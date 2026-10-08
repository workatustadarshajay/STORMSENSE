# Databricks notebook source
# MAGIC %md
# MAGIC # 10 App access
# MAGIC
# MAGIC Gives the app's service principal the least access it needs: read everything it shows, and write only the transfer decisions and
# MAGIC audit trail. Run after the app exists, with its service principal client id.

# COMMAND ----------

import os
import sys

# The shared library sits one folder up from the notebooks.
sys.path.insert(0, os.path.dirname(os.path.dirname("/Workspace" + dbutils.notebook.entry_point.getDbutils().notebook().getContext().notebookPath().get())))

import re

from stormsense_core import dbx
from stormsense_core.tables import TABLES

ctx = dbx.Ctx(spark, dbutils)
dbutils.widgets.text("app_service_principal", "", "App service principal (client id)")
sp = dbutils.widgets.get("app_service_principal").strip()
if not re.fullmatch(r"[\w\-.@]+", sp):
    raise ValueError("Pass the app's service principal client id")

# COMMAND ----------

write = {"transfer_recommendations", "transfer_audit"}
spark.sql(f"GRANT USE CATALOG ON CATALOG `{ctx.catalog}` TO `{sp}`")
spark.sql(f"GRANT USE SCHEMA ON SCHEMA `{ctx.catalog}`.`{ctx.schema}` TO `{sp}`")
for name in TABLES:
    privileges = "SELECT, MODIFY" if name in write else "SELECT"
    spark.sql(f"GRANT {privileges} ON TABLE {ctx.fq(name)} TO `{sp}`")
print(f"Granted {sp}: read on {len(TABLES) - len(write)} tables, read and write on {sorted(write)}")
