"""Writes the API description the frontend's types are generated from.

Run from backend/:  python scripts/export_openapi.py ../frontend/openapi.json
"""
import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[1]))

from app.config import Settings  # noqa: E402
from app.main import create_app  # noqa: E402
from app.sources.mock import MockSource  # noqa: E402

spec = create_app(Settings(STORMSENSE_MODE="mock"), MockSource()).openapi()
Path(sys.argv[1]).write_text(json.dumps(spec, indent=2, sort_keys=True) + "\n")
