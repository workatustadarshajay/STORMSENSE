"""Your own data, over HTTP: upload a CSV or send rows from another system. Off unless STORMSENSE_INGEST_ENABLED=1.

There is no sign-in on these routes (the hackathon copy is single-customer and local). Changes still need the
same-origin header, and they replace one feed at a time. Turn this off anywhere more than one person can reach.
"""

from __future__ import annotations

import csv
import io
from typing import Any

from fastapi import APIRouter, Depends, Request
from pydantic import BaseModel, ConfigDict, Field

from .auth import problem, same_origin
from .ingest import FEEDS, MAX_ROWS, auto_mapping, check, template


def _on(request: Request) -> None:
    if not request.app.state.settings.ingest_enabled:
        raise problem(404, "off", "Uploading your own data is turned off on this copy.")


router = APIRouter(prefix="/api/ingest", tags=["your data"], dependencies=[Depends(_on)])


class Refusal(BaseModel):
    line: int
    reason: str


class UploadResult(BaseModel):
    feed: str
    kept: int
    refused: int
    refusals: list[Refusal] = Field(description="The first 20 refused rows, with the line number and the reason")
    missing_columns: list[str]
    ignored_columns: list[str]
    message: str


class UploadBody(BaseModel):
    model_config = ConfigDict(str_strip_whitespace=True)
    csv: str | None = Field(None, max_length=2_000_000, description="The whole CSV file as text, with the column names on the first line")
    xlsx_base64: str | None = Field(
        None, max_length=4_000_000, description="An Excel file (.xlsx), base64 encoded. Columns are matched by name"
    )
    mapping: dict[str, str] | None = Field(None, description="Your column name for each StormSense column, if the names differ")


class RowsBody(BaseModel):
    rows: list[dict[str, Any]] = Field(max_length=MAX_ROWS)
    mapping: dict[str, str] | None = None


class ColumnInfo(BaseModel):
    name: str
    kind: str
    required: bool
    help: str
    choices: list[str]


class FeedInfo(BaseModel):
    feed: str
    title: str
    what: str
    kept: int
    refused: int
    updated: str | None
    columns: list[ColumnInfo]
    template: str


def _feed(name: str):  # noqa: ANN202
    if name not in FEEDS:
        raise problem(404, "not_found", "There is no feed with that name.")
    return FEEDS[name]


def _result(feed, out, kept_now: int) -> UploadResult:  # noqa: ANN001
    if out.missing:
        message = "The file is missing columns: " + ", ".join(out.missing) + ". Nothing was kept."
    else:
        message = f"Kept {kept_now} rows. Refused {len(out.refused)}."
    return UploadResult(feed=feed.key, kept=kept_now, refused=len(out.refused),
                        refusals=[Refusal(**r) for r in out.refused[:20]], missing_columns=out.missing,
                        ignored_columns=out.ignored, message=message)


def _store(request: Request):  # noqa: ANN202
    return request.app.state.ingest


@router.get("/feeds", response_model=list[FeedInfo])
def feeds(request: Request) -> list[FeedInfo]:
    store = _store(request)
    status = {s["feed"]: s for s in store.status()}
    return [FeedInfo(
        feed=f.key, title=f.title, what=f.what, kept=status[f.key]["rows"], refused=status[f.key]["refused"],
        updated=status[f.key]["updated"],
        columns=[ColumnInfo(name=c.name, kind=c.kind, required=c.required, help=c.help, choices=list(c.choices)) for c in f.columns],
        template=template(f),
    ) for f in FEEDS.values()]


@router.post("/feeds/{feed}/upload", response_model=UploadResult, dependencies=[Depends(same_origin)])
def upload(feed: str, body: UploadBody, request: Request) -> UploadResult:
    f = _feed(feed)
    if (body.csv is None) == (body.xlsx_base64 is None):
        raise problem(422, "one_file", "Send one file: a CSV, or an Excel workbook.")
    if body.xlsx_base64 is not None:
        rows = _excel_rows(f.key, body.xlsx_base64)
    else:
        rows = list(csv.DictReader(io.StringIO(body.csv)))
    if len(rows) > MAX_ROWS:
        raise problem(422, "too_many", f"A file can have at most {MAX_ROWS} rows. This one has {len(rows)}.")
    return _apply(f, rows, body.mapping, request)


@router.post("/feeds/{feed}/rows", response_model=UploadResult, dependencies=[Depends(same_origin)])
def rows_in(feed: str, body: RowsBody, request: Request) -> UploadResult:
    """Send rows from another system as JSON. Same checks as a file upload."""
    f = _feed(feed)
    rows = [{k: "" if v is None else str(v) for k, v in r.items()} for r in body.rows]
    return _apply(f, rows, body.mapping, request)


def _excel_rows(feed: str, encoded: str) -> list[dict[str, str]]:
    import base64
    import binascii
    import zipfile

    from .ingest import read_xlsx

    try:
        return read_xlsx(base64.b64decode(encoded, validate=True), feed)
    except (binascii.Error, zipfile.BadZipFile, KeyError, ValueError):
        raise problem(422, "not_excel", "That Excel file could not be read. Save it as .xlsx and try again.") from None


def _apply(f, rows: list[dict[str, str]], mapping: dict[str, str] | None, request: Request) -> UploadResult:  # noqa: ANN001
    store = _store(request)
    try:
        out = check(f, rows, mapping, store.known())
    except ValueError as e:  # personal or card columns
        raise problem(422, "not_accepted", str(e)) from None
    if not out.missing:
        store.save(f.key, out, {**auto_mapping(f, list(rows[0].keys()) if rows else []), **(mapping or {})})
    return _result(f, out, len(out.accepted) if not out.missing else 0)


class AnalysisItem(BaseModel):
    store: str
    product: str
    on_hand: int
    sold_per_day: float
    days_of_cover: float | None
    status: str = Field(description="Short (under 7 days), Watch (under 21 days), Plenty, or No sales")
    stock_value_usd: float
    sales_value_usd: float


class AnalysisStore(BaseModel):
    store: str
    short_items: int
    stock_value_usd: float


class Analysis(BaseModel):
    as_of: str
    window_days: int
    stores: int
    products: int
    pairs: int
    short: int
    watch: int
    sold_units: int
    sales_value_usd: float
    stock_value_usd: float
    by_store: list[AnalysisStore]
    items: list[AnalysisItem] = Field(description="The short and watch items, most urgent first")


@router.get("/analysis", response_model=Analysis)
def analysis(request: Request) -> Analysis:
    """A plain analysis of your uploaded data. Needs the stores, products, sales and stock files."""
    from .ingest_analysis import analyse

    result = analyse(_store(request))
    if result is None:
        raise problem(404, "not_ready", "Upload your stores, products, daily sales and daily stock files first.")
    return Analysis(**result)


@router.get("/feeds/{feed}/preview")
def preview(feed: str, request: Request, limit: int = 20) -> list[dict[str, Any]]:
    _feed(feed)
    saved = _store(request).read(feed)
    return (saved["rows"][: max(1, min(limit, 100))] if saved else [])


@router.delete("/feeds/{feed}", dependencies=[Depends(same_origin)])
def clear(feed: str, request: Request) -> dict[str, str]:
    _feed(feed)
    _store(request).clear(feed)
    return {"message": "Cleared. The planning screens will use the sample data for this file again."}
