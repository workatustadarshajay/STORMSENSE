# Running the app on your machine

The web app and the API run side by side. The API reads and writes the Databricks workspace; the web app talks only to the API.

| Piece | Command | Address |
|---|---|---|
| API (FastAPI) | `make dev-api` | http://localhost:8000 |
| Web app (React) | `make dev-web` | http://localhost:5173 (sends `/api` to the API) |
| Both | `make dev` | open http://localhost:5173 |

## Once: set up

Requirements: Python 3.12 with [uv](https://docs.astral.sh/uv/), Node.js 22, and, for real data, the Databricks CLI signed in:

```bash
make setup                                   # Python environment and web dependencies
databricks auth profiles                     # the profile "stormsense" should show Valid = YES
# if not:  databricks auth login --host https://<your-workspace>.cloud.databricks.com --profile stormsense
```

## Run on the real Databricks data

`backend/.env` tells the API which workspace to use. It holds no secrets (sign-in comes from the CLI profile) and is git-ignored:

```ini
STORMSENSE_MODE=databricks
STORMSENSE_DATABRICKS_PROFILE=stormsense
DATABRICKS_WAREHOUSE_ID=<your SQL warehouse id>      # databricks warehouses list --profile stormsense
DATABRICKS_GENIE_SPACE_ID=<your Ask space id>        # printed by databricks/scripts/create_genie_space.py
STORMSENSE_CATALOG=workspace
STORMSENSE_SCHEMA=stormsense
STORMSENSE_DEV_USER_EMAIL=<your workspace email>     # who you are when running locally
# Optional: the chat model behind Storm desk. Default databricks-gpt-5-mini; databricks-gpt-5-4-mini also works.
# STORMSENSE_AGENT_MODEL=databricks-gpt-5-mini
```

Then:

```bash
make dev
```

The API log must say `StormSense is using the Databricks workspace`. If it says `SAMPLE data`, `backend/.env` is missing or `STORMSENSE_MODE` is not `databricks`.

**What "real" means here.** The connection, tables, forecaster, jobs and permissions are all real and live in your workspace. The numbers inside are the generated sample dataset the build job wrote (there are no retail feeds connected yet), so the app shows a small **Sample data** label. Replace the feed tables with your own and the label goes away (see [go-live](go-live.md)).

**These are real writes.** Approving or rejecting a transfer in the app updates `transfer_recommendations` and writes `transfer_audit` in the workspace, exactly as it would in production. Your role comes from the `app_users` table, so `STORMSENSE_DEV_USER_EMAIL` must be a row there (the build job adds the deploying user as `admin`).

To put a transfer back to pending while demoing (this is an owner-only database edit, not something the app can do):

```sql
UPDATE workspace.stormsense.transfer_recommendations
SET status = 'PENDING', decided_by = NULL, decided_at = NULL, decision_note = NULL, decision_request_id = NULL
WHERE rec_id = 'TR-XXXXXXXXXX';
```

## Run on sample data (no workspace needed)

```bash
make dev-sample        # same screens, data served from fixtures; nothing is written anywhere
```

Or delete `backend/.env`. To see the read-only experience, set `STORMSENSE_DEV_USER_EMAIL=sam.viewer@stormsense.test`.

## Without `make`

Two terminals, from the repository root:

```bash
# 1. API
cd backend && ../.venv/bin/python -m uvicorn app.main:create_default_app --factory --reload --port 8000

# 2. Web app
cd frontend && npm run dev
```

## As one process, the way it ships

The deployed app is the API serving the built web app, with no second server:

```bash
make build-app                                  # builds the web app into backend/static
cd backend && ../.venv/bin/python -m app.main   # http://localhost:8000
```

## Storm desk (AI agent)

Open **Transfers > Get a plan from storm desk**, or go to http://localhost:5173/storm-desk. Type a goal such as "Prepare Florida for Sunday's storm". Storm desk checks the overview, stock risks, pending transfers and store forecasts, then writes a short plan that names only real pending transfers. It cannot approve, reject or change anything. Every check it made is listed under "What storm desk checked". It needs the live workspace; with sample data it says so.

Each plan calls a chat model in the workspace, so it uses a small amount of Databricks usage per question. Its checks are read-only queries, and the agent code is `backend/app/agent.py`.

## Tests

```bash
make test      # library, API and web tests (none of them touch the workspace)
make lint
make e2e       # browser tests; always on sample data, because they approve transfers
make smoke WAREHOUSE_ID=<id> SPACE_ID=<id>      # live check of the real workspace, read-only
```

## If something goes wrong

| What you see | Why, and what to do |
|---|---|
| The API hangs for minutes on the first request behind a company proxy | Python does not trust the proxy's certificate. `make` already points Python at the system certificates; if you start the API another way, set `REQUESTS_CA_BUNDLE=/etc/ssl/certs/ca-certificates.crt` first. |
| "Getting things ready" in the app | The serverless SQL warehouse is starting. It retries by itself and clears in seconds. |
| Ask says "Questions aren't available right now" | `DATABRICKS_GENIE_SPACE_ID` is missing from `backend/.env`. Run `databricks genie list-spaces --profile stormsense` to find the id, add it, and restart the API. |
| "That didn't load" | A query failed. The cause is in the API's terminal output, with the statement id. |
| `Address already in use` | A previous run is still up: `fuser -k 8000/tcp 5173/tcp`. |
| `databricks auth profiles` shows Valid = NO | Sign in again with the `databricks auth login` command above. |
| The page shows sample data but you expected live data | Check the API log line described above. |
