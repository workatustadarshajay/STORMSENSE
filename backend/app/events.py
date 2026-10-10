"""A plain log of what happened and when: uploads, plan builds, cost changes and planner decisions.

One JSON line per event, in a file next to the uploads. It feeds the business impact timeline.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import Any

LOG_FILE = "events.jsonl"


def record(folder: Path, kind: str, actor: str, **detail: Any) -> dict[str, Any]:
    folder.mkdir(parents=True, exist_ok=True)
    event = {"at": datetime.now().isoformat(timespec="seconds"), "kind": kind, "actor": actor, **detail}
    with (folder / LOG_FILE).open("a", encoding="utf-8") as f:
        f.write(json.dumps(event, default=str) + "\n")
    return event


def read(folder: Path, limit: int = 50) -> list[dict[str, Any]]:
    path = folder / LOG_FILE
    if not path.exists():
        return []
    lines = path.read_text(encoding="utf-8").splitlines()
    return [json.loads(line) for line in lines[-limit:] if line.strip()][::-1]
