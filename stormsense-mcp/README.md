# StormSense MCP server

Exposes the StormSense API as **MCP tools** (Model Context Protocol, Streamable HTTP). Any MCP-capable
assistant, agent framework or existing app can read the storm plan, ask questions, run a what-if, and
approve or reject transfers, without a StormSense screen.

## Architecture

The server holds no data and no database connection. Every call goes through the StormSense API, so its
roles, rate limits, read-only rules and audit trail still apply.

```
MCP client ──Streamable HTTP──> stormsense-mcp/server.py (FastMCP, port 8200)
                                    │ httpx
                                    ▼
                         StormSense API (backend, /api/...) ──> Databricks
```

### Configuration (env vars)

| Variable               | Default                       | Purpose                                              |
| ---------------------- | ----------------------------- | ---------------------------------------------------- |
| `STORMSENSE_API_URL`   | `http://localhost:8000/api`   | StormSense API base URL                              |
| `STORMSENSE_MCP_USER`  | `ava.planner@stormsense.test` | The account the calls act as. Its role decides what writes are allowed |

The API trusts the `X-Forwarded-Email` header only behind its sign-in proxy. In production, run this server
inside the same trusted network as the app, or give it a service identity through that proxy. Never expose
this server directly to the internet with a planner identity set.

### Tools

| Tool | Kind | What it does |
| --- | --- | --- |
| `stormsense_overview` | read | Urgent transfers, transfers waiting, stores at risk, next alert |
| `stormsense_list_transfers` | read | Transfers filtered by status and urgency (default: pending) |
| `stormsense_get_transfer` | read | One transfer by id, with its reason |
| `stormsense_list_stores` | read | Stores in the network |
| `stormsense_store_forecast` | read | A store's seven-day demand forecast |
| `stormsense_ask` | read | Plain-English question answered from the live data |
| `stormsense_what_if` | read | Storm cost estimate; changes no data |
| `stormsense_storm_desk_plan` | read | The storm desk crew's plan (about a minute); approves nothing |
| `stormsense_approve_transfers` | **write** | Approves pending transfers. Needs a planner account; the API checks it |
| `stormsense_reject_transfers` | **write** | Rejects pending transfers with a reason. The daily run learns from it |

Inputs are checked before any call: transfer ids must match `TR-XXXXXXXXXX`, store ids `SNN`. Errors come back
as `{"ok": false, "error": "..."}` with the API's own message (for example, a viewer account asking to approve).

## Run

```bash
# 1. Start the StormSense API (from the repository root)
cd backend && ../.venv/bin/python -m uvicorn app.main:create_default_app --factory --port 8000

# 2. Start the MCP server
cd stormsense-mcp
STORMSENSE_API_URL=http://localhost:8000/api uv run --system-certs uvicorn server:app --port 8200
```

- MCP endpoint: `http://localhost:8200/mcp` (Streamable HTTP)
- Health probe: `http://localhost:8200/health`

## Demo client

`demo_client.py` is a dependency-free MCP client (urllib, JSON-RPC 2.0) that runs the integration story against
the running server.

```bash
uv run python demo_client.py                 # read-only: handshake, tools, overview, transfers, what-if
uv run python demo_client.py --agent         # also the storm desk plan (about a minute, live data only)
uv run python demo_client.py --approve       # also approves one urgent transfer (changes data)
```

To connect an assistant instead, point its MCP settings at `http://localhost:8200/mcp`.

## MCP client agent (`mcp_agent.py`)

A client that uses the tools itself. It connects to the MCP server, discovers the tools, and lets a
chat model choose which to call. Each check is printed to the terminal as it happens.

```bash
uv run python mcp_agent.py "Which stores are at risk today, and what should planners do first?"
```

- **Model access:** the model is served by the workspace (default `databricks-gemini-3-5-flash`). It uses
  the same CLI sign-in as the rest of the project, so no separate Google or model API key is needed.
  Set `STORMSENSE_MCP_MODEL` to use another workspace model.
- **Read-only by default.** The approve and reject tools are hidden from the model unless you set `ALLOW_WRITES=1`.
- **Limits:** at most six model steps; on the last step no tools are offered, so it has to answer.

## Tests

```bash
uv run --group dev pytest -q     # tool calls checked against a stand-in API; no network needed
```

## Notes

- Sample-mode APIs say that the what-if and storm desk need the live workspace; those tools report that message.
- The approve and reject tools change live data when the API is in live mode. Test them against a sample-mode API first.
