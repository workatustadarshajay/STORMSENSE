# Databricks notebook source
# MAGIC %md
# MAGIC # 15 Demo storm alert
# MAGIC
# MAGIC Started by the **Email this storm alert** button on the StormSense Today page. It does nothing except finish, so
# MAGIC Databricks emails the alert address when the run succeeds. It has no schedule and runs only when someone clicks.

# COMMAND ----------

dbutils.notebook.exit("demo storm alert sent")
