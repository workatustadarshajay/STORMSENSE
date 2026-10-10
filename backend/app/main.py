"""App factory: API, security middleware and (when built) the web app, all from one process."""
from __future__ import annotations

import logging
import os
from pathlib import Path

import uvicorn
from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import FileResponse, JSONResponse

from .agent import ModelClient, StormDesk
from .api import router
from .config import Settings, get_settings
from .dbx import QueryError, Warehouse, WarmingUp
from .security import BodyLimit, RateLimiter, SecurityHeaders
from .service import Service
from .sources.base import DataSource
from .whatif import EndpointScorer

log = logging.getLogger("stormsense")


def build_source(settings: Settings) -> DataSource:
    if settings.mode == "mock":
        from .sources.mock import MockSource

        return MockSource()
    if not settings.warehouse_id:
        raise RuntimeError("DATABRICKS_WAREHOUSE_ID is required when STORMSENSE_MODE=databricks")
    from databricks.sdk import WorkspaceClient

    from .sources.databricks import DatabricksSource

    client = WorkspaceClient(profile=settings.databricks_profile) if settings.databricks_profile else WorkspaceClient()
    sql = Warehouse(client, settings.warehouse_id, settings.catalog, settings.schema_name, settings.query_budget_seconds)
    return DatabricksSource(sql, client.genie, settings.genie_space_id, settings.ask_timeout_seconds)


def build_storm_desk(settings: Settings, service: Service) -> StormDesk | None:
    """Storm desk needs a chat model in the workspace, so it exists only in databricks mode."""
    if settings.mode != "databricks":
        return None
    from databricks.sdk import WorkspaceClient

    client = WorkspaceClient(profile=settings.databricks_profile) if settings.databricks_profile else WorkspaceClient()
    return StormDesk(service, ModelClient(client.api_client, settings.storm_desk_model))


def build_workspace(settings: Settings):  # noqa: ANN201
    """The workspace client the app uses for jobs (the demo email). None with sample data."""
    if settings.mode != "databricks":
        return None
    from databricks.sdk import WorkspaceClient

    return WorkspaceClient(profile=settings.databricks_profile) if settings.databricks_profile else WorkspaceClient()


def build_forecast_scorer(settings: Settings) -> EndpointScorer | None:
    """The forecaster's serving endpoint scores the what-if rows. It exists only in databricks mode."""
    if settings.mode != "databricks":
        return None
    from databricks.sdk import WorkspaceClient

    client = WorkspaceClient(profile=settings.databricks_profile) if settings.databricks_profile else WorkspaceClient()
    return EndpointScorer(client.api_client, settings.forecast_endpoint)


def create_app(settings: Settings | None = None, source: DataSource | None = None) -> FastAPI:
    settings = settings or get_settings()
    app = FastAPI(title="StormSense", version="1.0.0", docs_url=None, redoc_url=None, openapi_url="/api/openapi.json")
    app.state.settings = settings
    # One service per data source. The browser picks one per request (X-Data-Source); the default is the copy's mode.
    default = "live" if settings.mode == "databricks" else "sample"
    if source is not None:
        services = {default: Service(source, settings)}
    elif settings.mode == "databricks":
        from .sources.mock import MockSource

        services = {"live": Service(build_source(settings), settings), "sample": Service(MockSource(), settings)}
    else:
        services = {"sample": Service(build_source(settings), settings)}
    app.state.services = services
    app.state.default_source = default
    app.state.service = services[default]
    app.state.limiter = RateLimiter(settings.ask_per_minute)
    app.state.desk_limiter = RateLimiter(5)
    app.state.storm_desk = build_storm_desk(settings, services["live"]) if "live" in services else None
    app.state.workspace = build_workspace(settings)
    if settings.ingest_enabled:
        from .ingest import IngestStore

        app.state.ingest = IngestStore(settings.ingest_dir)
        if settings.ingest_drop:
            from .ingest import start_drop_watcher

            start_drop_watcher(app.state.ingest)
        from .ingest_plan import PLAN_FILE

        plan_file = settings.ingest_dir / PLAN_FILE
        if plan_file.exists():  # a plan built from uploads in an earlier run
            from .sources.mock import MockSource

            services["upload"] = Service(MockSource(plan_file), settings)
    app.state.what_if_limiter = RateLimiter(6)
    app.state.alert_limiter = RateLimiter(3)
    app.state.forecast_scorer = build_forecast_scorer(settings)

    app.add_middleware(BodyLimit, max_bytes=settings.max_body_bytes)
    app.add_middleware(SecurityHeaders, production=settings.environment == "production")
    app.include_router(router)
    from .ingest_api import router as ingest_router

    app.include_router(ingest_router)

    @app.exception_handler(WarmingUp)
    async def warming(_: Request, __: WarmingUp) -> JSONResponse:
        message = "Getting things ready. This usually takes a few seconds."
        return JSONResponse({"detail": {"code": "warming_up", "message": message}}, status_code=503, headers={"Retry-After": "5"})

    @app.exception_handler(QueryError)
    async def failed(_: Request, __: QueryError) -> JSONResponse:
        message = "We couldn't load that right now. Please try again."
        return JSONResponse({"detail": {"code": "unavailable", "message": message}}, status_code=502)

    @app.exception_handler(RequestValidationError)
    async def invalid(_: Request, __: RequestValidationError) -> JSONResponse:
        message = "Please check what you entered and try again."
        return JSONResponse({"detail": {"code": "invalid", "message": message}}, status_code=422)

    if (settings.ingest_client_dir / "index.html").is_file():
        from fastapi.staticfiles import StaticFiles

        app.mount("/ingest", StaticFiles(directory=settings.ingest_client_dir, html=True), name="ingestion-client")
    _serve_web_app(app, settings.static_dir)
    return app


def _serve_web_app(app: FastAPI, root: Path) -> None:
    index = root / "index.html"
    if not index.is_file():
        return
    root = root.resolve()

    @app.get("/{path:path}", include_in_schema=False)
    def web(path: str) -> FileResponse:
        target = (root / path).resolve()
        if target.is_file() and root in target.parents:
            return FileResponse(target)
        return FileResponse(index)  # client-side routes


def create_default_app() -> FastAPI:
    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(name)s %(message)s")
    settings = get_settings()
    where = f"the Databricks workspace (warehouse {settings.warehouse_id})" if settings.mode == "databricks" else "SAMPLE data"
    log.info("StormSense is using %s", where)
    return create_app(settings)


if __name__ == "__main__":
    uvicorn.run(create_default_app(), host="0.0.0.0", port=int(os.environ.get("DATABRICKS_APP_PORT", 8000)))  # noqa: S104
