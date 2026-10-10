# Running the app on your machine

The web app and the API run side by side. The API reads and writes the Databricks workspace; the web app talks only to the API.

| Piece | Command | Address |
|---|---|---|
| Planner app: API (FastAPI) | `make dev-api` | http://localhost:8000 |
| Planner app: web (React) | `make dev-web` | http://localhost:5173 (sends `/api` to the API) |
| Ingestion client | `make dev-ingest` | http://localhost:5174 |
| All three apps | `make dev` (or `make dev-sample` on sample data) | open http://localhost:5173 and http://localhost:5174 |

The MCP server is separate: `make dev-mcp` starts it on http://localhost:8200/mcp when you want an AI assistant to connect.

**Sample or live data.** The **Data shown** switch in the sidebar changes every screen between the generated sample data and the live workspace. It is available only where the live workspace is connected (`backend/.env` set up). Your choice is remembered in the browser.

`make setup` installs everything, including the ingestion client and the MCP server. Uploads are switched on for the local API in `make dev`, so the ingestion client works straight away.

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

## What-if simulator

Open **Transfers > What if a storm comes?**, or go to http://localhost:5173/what-if. Set the strength, when it hits, how many days, and where. It shows the sales that would be lost if nothing moved and the stock that would need to move. It calls the forecaster's serving endpoint and changes nothing.

It uses the endpoint named by `STORMSENSE_FORECAST_ENDPOINT` (default `stormsense-forecaster`). That endpoint scales to zero, so the first simulation after a quiet period can take a minute.

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
| What-if says "needs the live workspace" | Expected with sample data. Set `STORMSENSE_MODE=databricks` in `backend/.env`. |
| Ask says "Questions aren't available right now" | `DATABRICKS_GENIE_SPACE_ID` is missing from `backend/.env`. Run `databricks genie list-spaces --profile stormsense` to find the id, add it, and restart the API. |
| "That didn't load" | A query failed. The cause is in the API's terminal output, with the statement id. |
| `Address already in use` | A previous run is still up: `fuser -k 8000/tcp 5173/tcp`. |
| `databricks auth profiles` shows Valid = NO | Sign in again with the `databricks auth login` command above. |
| The page shows sample data but you expected live data | Check the API log line described above. |

## Live or demo weather

Today has a **Weather** switch. **Live weather** shows the real forecast. **Demo storm** places a storm on the Florida stores for the next two days, so you can show what a storm would do to alerts, readiness and the store forecast. The banner says the stock figures and transfers still come from the live plan. It needs no redeploy and changes nothing in the data.

To change the data the daily job uses, set the bundle variable `weather_provider` (`nws` for the live forecast, `sample` for generated weather). That changes the plan the next time the job runs.


## Demo storm email

On Today, with **Demo storm** selected, **Email this storm alert** starts the Databricks job `StormSense - Demo storm alert`. Databricks then emails the alert address (given at deploy time with `--var alert_email=...`). No mail server or password is needed. The job has no schedule and runs only on click.

Until the bundle is deployed, the button says the job isn't in the workspace yet. The button needs the live workspace; sample data cannot start jobs.

## Demo: your data, end to end

1. `make dev`, then open the upload app at http://localhost:5174.
2. Click **Load the sample data (one click)**. The four sample workbooks load, and the checks say what they found.
3. Click **Build the plan from my files**. The plan uses a simple forecast (the average sales on each weekday over the last four weeks), the stock gaps and the transfers, and shows the estimated profit.
4. Click **Open the planner on my data**. The planner's **Your uploads** source is selected, so Today, Transfers and the stores show the plan built from your files. The sidebar says **Your data**.
5. On the upload app, the **Analysis** section shows the products running short, and the **Email the planners** button sends the email when the live workspace is connected.

To use your own files, download the Excel template for each feed. Store and product codes are dropdowns filled from the files you loaded, so unknown codes are refused in the template. Upload the four files, then build the plan again.

Files can also be dropped in `backend/data/ingest/drop/` (named `stores`, `products`, `sales` or `stock`, as CSV or Excel). They load when the server is started with `STORMSENSE_INGEST_DROP=1`, or straight away with **Load files from the drop folder now**.

Approving or rejecting a markdown suggestion records the decision for the planner. These decisions are kept in memory, so they reset when the server restarts.

## Your own data: the ingestion client

The **ingestion client** is a separate small front end for connecting your data. It uses the same backend, so it needs the server setting `STORMSENSE_INGEST_ENABLED=1` and a restart. Keep that setting off anywhere other people can reach, because uploads have no sign-in.

```bash
cd ingestion-client && npm install
npm run dev          # http://localhost:5174, forwards to the backend on port 8000
npm run build        # then the backend serves it at http://localhost:8000/ingest/
```

Upload four CSV files, in this order: stores, products, daily sales, daily stock. Each file is checked row by row, and refused rows show the line and the reason. Other systems can send the same rows as JSON. Uploaded files are kept under `backend/data/ingest/`, which is not committed.

The planning screens still show the sample data. Connecting uploaded files to them is the next step.

The upload app now shows **Your data in pictures**: sales and stock by day, days of stock left by store, and the status of each store and product. The planner has an **Analysis** page with the plan in pictures, and a **Business impact** page with the figures, the decisions, the assumptions and a timeline of updates. The timeline is kept in `backend/data/ingest/events.jsonl`, which is not committed.

