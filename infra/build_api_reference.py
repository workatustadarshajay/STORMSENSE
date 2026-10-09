"""Writes docs/api-reference.md from the API's OpenAPI description (frontend/openapi.json).

Run after the API changes, after `make types` has refreshed frontend/openapi.json:
    python3 infra/build_api_reference.py
"""

from __future__ import annotations

import json
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SPEC = ROOT / "frontend" / "openapi.json"
OUT = ROOT / "docs" / "api-reference.md"

METHOD_ORDER = ["get", "post", "patch", "put", "delete"]
CONSTRAINTS = {
    "minLength": "min length {}",
    "maxLength": "max length {}",
    "minItems": "at least {} items",
    "maxItems": "at most {} items",
    "minimum": "≥ {}",
    "maximum": "≤ {}",
    "pattern": "matches `{}`",
    "default": "default `{}`",
}


def resolve(spec: dict, schema: dict) -> dict:
    """Follow one $ref to the component it names."""
    if "$ref" in schema:
        return spec["components"]["schemas"][schema["$ref"].rsplit("/", 1)[-1]]
    return schema


def describe(spec: dict, schema: dict) -> str:
    """Short type name for a schema: `string`, `list of Transfer`, `one of: a, b`, and so on."""
    if "$ref" in schema:
        return schema["$ref"].rsplit("/", 1)[-1]
    if "anyOf" in schema:
        parts = [describe(spec, s) for s in schema["anyOf"] if s.get("type") != "null"]
        return " or ".join(parts) + (" (optional)" if any(s.get("type") == "null" for s in schema["anyOf"]) else "")
    if "enum" in schema:
        return "one of " + ", ".join(f"`{v}`" for v in schema["enum"])
    if schema.get("type") == "array":
        return "list of " + describe(spec, schema.get("items", {}))
    return schema.get("type", "any")


def notes(schema: dict) -> str:
    bits = [text.format(json.dumps(schema[key])) for key, text in CONSTRAINTS.items() if key in schema]
    if "description" in schema:
        bits.insert(0, schema["description"])
    return "; ".join(bits)


def fields_table(spec: dict, model: dict, required: set[str] | None = None) -> list[str]:
    """Request fields show whether they are required; response fields (required=None) leave that column out."""
    if required is None:
        rows = ["| Field | Type | Notes |", "|---|---|---|"]
    else:
        rows = ["| Field | Type | Required | Notes |", "|---|---|---|---|"]
    for name, prop in model.get("properties", {}).items():
        cells = [f"`{name}`", describe(spec, prop)]
        if required is not None:
            cells.append("yes" if name in required else "no")
        cells.append(notes(resolve(spec, prop)) or "")
        rows.append("| " + " | ".join(cells) + " |")
    return rows


def endpoint_section(spec: dict, path: str, method: str, op: dict) -> list[str]:
    lines = [f"### `{method.upper()} {path}`", ""]
    if op.get("summary"):
        lines += [op["summary"], ""]
    if op.get("description"):
        lines += [op["description"].strip(), ""]

    params = [p for p in op.get("parameters", []) if p.get("in") in ("path", "query")]
    if params:
        lines += ["**Parameters**", "", "| Name | In | Type | Required | Notes |", "|---|---|---|---|---|"]
        for p in params:
            schema = p.get("schema", {})
            lines.append(
                f"| `{p['name']}` | {p['in']} | {describe(spec, schema)} | "
                f"{'yes' if p.get('required') else 'no'} | {notes(resolve(spec, schema)) or ''} |"
            )
        lines.append("")

    body = op.get("requestBody", {}).get("content", {}).get("application/json", {}).get("schema")
    if body:
        model = resolve(spec, body)
        lines += ["**Request body**", ""]
        lines += fields_table(spec, model, set(model.get("required", [])))
        lines.append("")

    reply = op.get("responses", {}).get("200", {}).get("content", {}).get("application/json", {}).get("schema")
    if reply:
        lines += ["**Response**", "", f"Returns {describe(spec, reply)}.", ""]
        model = resolve(spec, reply)
        if model.get("properties"):
            lines += fields_table(spec, model)
            lines.append("")
    return lines


def build() -> str:
    spec = json.loads(SPEC.read_text())
    lines = [
        "# API reference",
        "",
        "Every endpoint the web app and the MCP server call. This page is generated from the API's own description "
        f"(`frontend/openapi.json`, version {spec['info']['version']}), so it matches the code.",
        "",
        "!!! note \"Who can call what\"",
        "    Reading is open to anyone who can sign in. Approving and rejecting need a planner or admin account. "
        "Storm desk, Ask and the what-if are rate-limited per person. Every write needs the `X-Requested-With: stormsense` header.",
        "",
        "Errors come back as `{\"detail\": {\"code\": \"...\", \"message\": \"...\"}}` with a plain-language message.",
        "",
    ]
    for path, methods in spec["paths"].items():
        for method in METHOD_ORDER:
            if method in methods:
                lines += endpoint_section(spec, path, method, methods[method])
    return "\n".join(lines).rstrip() + "\n"


if __name__ == "__main__":
    OUT.write_text(build())
    print(f"wrote {OUT.relative_to(ROOT)}")
