"""Thin Spark helpers for the notebooks. Imported only inside Databricks."""
from __future__ import annotations

import re
from datetime import date

import pandas as pd

from .reference import SETTINGS


class Ctx:
    """Catalog and schema from widgets, plus read/write helpers that keep tables typed and writes idempotent."""

    def __init__(self, spark, dbutils):  # noqa: ANN001
        self.spark = spark
        self.dbutils = dbutils
        dbutils.widgets.text("catalog", "", "Catalog (blank = workspace default)")
        dbutils.widgets.text("schema", "stormsense", "Schema")
        self.catalog = dbutils.widgets.get("catalog").strip() or spark.sql("SELECT current_catalog()").first()[0]
        self.schema = dbutils.widgets.get("schema").strip()
        for part in (self.catalog, self.schema):
            if not re.fullmatch(r"[\w\-]+", part):
                raise ValueError(f"Unsafe catalog or schema name: {part!r}")

    def fq(self, name: str) -> str:
        return f"`{self.catalog}`.`{self.schema}`.`{name}`"

    def read(self, name: str) -> pd.DataFrame:
        return self.spark.table(self.fq(name)).toPandas()

    def frame(self, pdf: pd.DataFrame, name: str):  # noqa: ANN201
        """A Spark DataFrame typed like the existing table `name`."""
        schema = self.spark.table(self.fq(name)).schema
        return self.spark.createDataFrame(_conform(pdf, schema), schema=schema)

    def write(self, pdf: pd.DataFrame, name: str, replace_where: str | None = None, new_schema: bool = False) -> int:
        """Overwrite a table, or just the slice matching `replace_where` (idempotent re-runs)."""
        sdf = self.spark.createDataFrame(pdf) if new_schema else self.frame(pdf, name)
        w = sdf.write.format("delta").mode("overwrite")
        if replace_where:
            w = w.option("replaceWhere", replace_where)
        if new_schema:
            w = w.option("overwriteSchema", "true")
        w.saveAsTable(self.fq(name))
        return len(pdf)

    def setting_values(self) -> dict[str, float]:
        rows = self.read("settings")
        found = {r.key: r.value for r in rows.itertuples()}
        return {k: float(found.get(k, default)) for k, default in SETTINGS.items()}

    def as_of(self) -> date:
        """The forecast origin: the last day of stock data, unless a run passes one explicitly."""
        self.dbutils.widgets.text("as_of_date", "", "As-of date (blank = latest stock snapshot)")
        given = self.dbutils.widgets.get("as_of_date").strip()
        if given:
            return date.fromisoformat(given)
        return self.spark.sql(f"SELECT max(snapshot_date) FROM {self.fq('inventory_snapshot')}").first()[0]


def _conform(pdf: pd.DataFrame, schema) -> pd.DataFrame:  # noqa: ANN001
    """Cast pandas columns to the table's Spark types so nullable and date columns write cleanly."""
    from pyspark.sql import types as T  # noqa: N812

    out = pd.DataFrame(index=pdf.index)
    for f in schema.fields:
        s, kind = pdf[f.name], f.dataType
        if isinstance(kind, (T.LongType, T.IntegerType)):
            s = s.round().astype("Int64")
        elif isinstance(kind, T.DoubleType):
            s = s.astype("float64")
        elif isinstance(kind, T.BooleanType):
            s = s.astype("boolean")
        elif isinstance(kind, T.TimestampType):
            s = pd.to_datetime(s)
        elif isinstance(kind, T.DateType):
            d = pd.to_datetime(s).dt.date.astype(object)
            s = d.where(pd.to_datetime(s).notna(), None)
        else:
            s = s.astype(object).where(s.notna(), None)
        out[f.name] = s
    return out
