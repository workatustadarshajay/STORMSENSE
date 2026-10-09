# Connect StormSense to your app

StormSense can be used in three ways. Pick the one that matches what your app already does.

| You want to... | Use | You build | You get |
|---|---|---|---|
| Let an AI assistant (Claude, ChatGPT, Gemini, or an agent framework) read the plan and ask questions | **MCP server** | Nothing. Point the assistant at the server | Ten tools: read the overview, transfers, stores, forecasts, what-if and the storm desk plan, plus approve and reject |
| Show StormSense data inside your own app (a dashboard, a store system, a mobile app) | **REST API** | The screens, using the API's documented endpoints | Everything the planner app uses, with the same rules |
| Give your team the full planning screens | **The StormSense web app** | Nothing. Open it in a browser | The complete planner experience |

## 1. Connect an AI assistant through MCP

The MCP server exposes StormSense as tools. Any client that speaks the Model Context Protocol can use them without reading any code. The server runs beside the API and calls it on your behalf, so the same roles, rate limits and audit trail apply.

**The server address:** `http://<host>:8200/mcp` (Streamable HTTP). Locally it is `http://localhost:8200/mcp`. A health check is at `/health`.

**Add it to an assistant** that supports remote MCP servers. The exact menu differs by product, but the entry is always a name and a URL:

```json
{
  "mcpServers": {
    "stormsense": { "type": "http", "url": "http://localhost:8200/mcp" }
  }
}
```

**The tools:**

| Tool | Kind | What it returns or does |
|---|---|---|
| `stormsense_overview` | read | Urgent moves, moves waiting, stores at risk, the next weather alert |
| `stormsense_list_transfers` | read | Moves filtered by status and urgency (defaults to pending) |
| `stormsense_get_transfer` | read | One move by its id, with its reason |
| `stormsense_list_stores` | read | Stores in the network |
| `stormsense_store_forecast` | read | A store's seven-day forecast |
| `stormsense_ask` | read | A plain-language question, answered from the data |
| `stormsense_what_if` | read | The cost of a storm if no stock moves. Changes nothing |
| `stormsense_storm_desk_plan` | read | The storm desk plan, which takes about a minute. Approves nothing |
| `stormsense_approve_transfers` | write | Approves pending moves. Needs a planner account |
| `stormsense_reject_transfers` | write | Rejects pending moves with a reason |

**Which account it acts as:** the server acts as the account in `STORMSENSE_MCP_USER`. Give it a planner account only if the assistant should approve moves. Otherwise give it a viewer account, and the write tools will be refused.

**Test it without an assistant:**
```bash
cd stormsense-mcp && uv run python demo_client.py      # lists the tools and reads the data
```

## 2. Build your own app on the REST API

The API is the same one the planner app uses. Its full description is in the [API reference](../api-reference.md), generated from the code so it always matches.

Start with the read endpoints:

```bash
curl -s http://localhost:8000/api/overview            # today's summary
curl -s http://localhost:8000/api/transfers           # all transfers
curl -s "http://localhost:8000/api/transfers?status=PENDING&urgency=URGENT"
curl -s http://localhost:8000/api/stores/S01/forecast
curl -s http://localhost:8000/api/transfers/export?status=PENDING   # the plan as CSV
```

**Writes need one extra header.** Every approve, reject, ask, storm desk and what-if call must send `X-Requested-With: stormsense`. Requests without it are refused. This blocks other websites from making changes in a browser.

**Identity.** The API reads who is calling from the `X-Forwarded-Email` header. In the deployed app, the sign-in proxy sets it, and the API is reachable only through that proxy. Your own backend must not set this header for people it has not signed in itself.

**Roles.** Reading is open to anyone the proxy lets in. Approving and rejecting need a planner or admin account. Accounts without a role are viewers.

**Limits.** Storm desk, Ask and the what-if are rate limited per person. Expect a `429` with a `Retry-After` header when you hit them.

**Errors.** Errors come back as `{"detail": {"code": "...", "message": "..."}}`. The message is written in plain language, so you can show it to a user.

## 3. Use the StormSense web app

Open the planner app in a browser. It is the full experience: Today, Transfers, Stores, Ask, Storm desk, What if, and History. Its address is the one your team was given, and it is only reachable with a work sign-in.

## Choosing

- **Your users talk to an AI assistant** → MCP. Nothing to build.
- **Your users already live in another system** (a store management tool, an ERP, a mobile app) → the REST API, showing only the parts they need.
- **Your users need every screen** → the web app.
- **You want both** → the MCP server and the API run side by side, and both sit behind the same sign-in.

## Security checklist for anyone building on it

- Give each integration its own account, with the smallest role it needs. Viewers can read; only planners can approve.
- Never put the API or the MCP server on the open internet. Put them behind the same sign-in as the planner app.
- Do not forward a person's identity header from your own system unless you have checked who they are.
- Keep secrets out of code. StormSense stores none; your integration should store its own in a secret store.
- Expect rate limits. Retry only after the `Retry-After` time.
- Show planners that approvals are theirs to make. The API and the MCP server both record who approved what.

## Status

Both the MCP server and the API run locally against the live workspace. The hosted deployment is still blocked by the company network filter, so an external system cannot reach them yet. The MCP server is ready to connect as soon as it is hosted. See [go-live](../go-live.md) for what is left.
