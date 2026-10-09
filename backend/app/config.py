"""Settings, read from environment variables (see infra/.env.example)."""
from __future__ import annotations

from functools import lru_cache
from pathlib import Path
from typing import Literal

from pydantic import Field
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore", populate_by_name=True)

    # "mock" serves realistic fixture data with no Databricks connection; "databricks" is the live workspace.
    mode: Literal["mock", "databricks"] = Field("mock", validation_alias="STORMSENSE_MODE")
    # "production" never trusts a local dev identity; the platform's sign-in headers are required.
    environment: Literal["local", "production"] = Field("local", validation_alias="STORMSENSE_ENVIRONMENT")

    catalog: str = Field("", validation_alias="STORMSENSE_CATALOG")
    schema_name: str = Field("stormsense", validation_alias="STORMSENSE_SCHEMA")
    warehouse_id: str = Field("", validation_alias="DATABRICKS_WAREHOUSE_ID")
    genie_space_id: str = Field("", validation_alias="DATABRICKS_GENIE_SPACE_ID")
    databricks_profile: str | None = Field(None, validation_alias="STORMSENSE_DATABRICKS_PROFILE")

    default_role: Literal["viewer", "planner", "admin"] = Field("viewer", validation_alias="STORMSENSE_DEFAULT_ROLE")
    dev_user_email: str = Field("ava.planner@stormsense.test", validation_alias="STORMSENSE_DEV_USER_EMAIL")

    # Chat model for storm desk. These answer tool calls in this workspace: databricks-gpt-5-mini, databricks-gpt-5-4-mini.
    storm_desk_model: str = Field("databricks-gpt-5-mini", validation_alias="STORMSENSE_AGENT_MODEL")
    # Serving endpoint that scores the what-if simulator (created from the forecaster, version 3).
    forecast_endpoint: str = Field("stormsense-forecaster", validation_alias="STORMSENSE_FORECAST_ENDPOINT")
    # Demo storm email: the Email button starts this Databricks job, and Databricks emails the job's alert address.
    demo_job_name: str = Field("StormSense - Demo storm alert", validation_alias="STORMSENSE_DEMO_JOB")
    # Your own data: uploads are off unless this is on. The hackathon copy has no sign-in, so keep it off where others can reach it.
    ingest_enabled: bool = Field(False, validation_alias="STORMSENSE_INGEST_ENABLED")
    ingest_client_dir: Path = Field(
        Path(__file__).resolve().parent.parent.parent / "ingestion-client" / "dist", validation_alias="STORMSENSE_INGEST_CLIENT_DIR"
    )
    ingest_dir: Path = Field(Path(__file__).resolve().parent.parent / "data" / "ingest", validation_alias="STORMSENSE_INGEST_DIR")
    cache_seconds: int = 30
    query_budget_seconds: int = 45
    ask_timeout_seconds: int = 60
    ask_per_minute: int = 10
    max_body_bytes: int = 64 * 1024
    static_dir: Path = Path(__file__).resolve().parent.parent / "static"

    @property
    def allow_dev_identity(self) -> bool:
        return self.environment == "local"


@lru_cache
def get_settings() -> Settings:
    return Settings()
