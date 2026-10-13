# High-level architecture

This page shows the whole of StormSense on one page, from the data a planner needs to the decisions the planner makes. The [interactive end-to-end diagram](https://workatustadarshajay.github.io/STORMSENSE/architecture/high-level.html) shows the same parts with the connections between them. The [system design](system-design.md) page explains the reasons behind the choices.

## The parts

| Part | Where it lives | What it does |
|---|---|---|
| Planners and store staff | Phone or laptop | Use the web app to review moves, approve or reject them, and ask questions |
| Data owner | Ingestion client (`ingestion-client/`) | Uploads the four feeds as CSV or sends rows as JSON |
| AI assistant | MCP server (`stormsense-mcp/`) | Reads the plan and acts on it through tools, under the same rules as the app |
| National Weather Service | Outside service | Supplies the forecast and the storm warnings |
| Sales and stock feeds | Planned | Real feeds that will replace the sample tables; not connected yet |
| Web app | `frontend/` | Today, Transfers, Stores, Ask, Storm desk, What if, History and more |
| API | `backend/` | The only part that talks to Databricks. Checks sign-in and roles, applies approvals, writes the audit trail |
| Workspace sign-in | Databricks Apps | Signs people in with their workspace account and sets their identity |
| Local uploads | `backend/data/ingest/` | Holds uploaded feeds in mock and local runs |
| SQL warehouse | Databricks | Runs the constant, parameterized queries the API sends |
| Delta tables | Unity Catalog, `stormsense` schema | Stores stores, products, sales, stock, forecasts, gaps, transfers and the audit trail |
| Daily job | Databricks, 6:00 AM Eastern | Refreshes weather, builds features, scores the forecast, finds gaps and recommends transfers, then verifies |
| Data quality gates | Lakeflow pipeline | Checks the data before the daily features are built |
| Storm trigger | Databricks, every 15 minutes | Checks NWS warnings and starts one daily run when a plan-changing warning appears. Paused by default |
| Forecaster endpoint | Model serving | Serves the forecaster registered as `champion`, for the daily run and the what-if simulator |
| Storm desk model | Model serving | Drafts the storm desk plan. It has read-only tools and cannot change data |
| Ask space | Genie, read-only | Answers free-form questions over a few tables. Cannot change anything |
| Storm alert email | Databricks job | Sends the demo storm alert when someone presses the button |

## End to end

1. **Data comes in.** The data owner uploads the four feeds through the ingestion client, or the sample tables stand in for them. Each row is checked, and refused rows come back with the line number and the reason. Uploads are off unless `STORMSENSE_INGEST_ENABLED=1`.
2. **Weather arrives.** Each morning the daily job asks the National Weather Service for a ten-day forecast per store. The storm trigger watches for warnings every 15 minutes and can start one extra run.
3. **Data is checked and turned into features.** The quality gates run first, then features are built from weather, sales and stock. Features only use what was known on the day.
4. **The forecaster scores the week.** It is loaded by the alias `champion` and writes seven days of forecast per store and product. Re-running a day replaces that day only.
5. **Gaps and moves are found.** Projected stock and days of cover show where a store will run short or has spare stock. Nearest-source matching turns that into transfer recommendations. A merge only refreshes pending rows, so decided rows are never overwritten.
6. **The daily run verifies itself.** If anything is wrong, the job fails loudly and emails the account that deployed it.
7. **A planner decides.** The planner signs in, sees Today, and reviews the moves. Approve and reject go through the API, which checks the role, changes only rows still pending, and writes an audit trail entry for every attempt.
8. **Questions and what-ifs.** Ask answers read-only over the tables. The what-if simulator scores a storm week against a normal week with the same forecaster and writes nothing. The storm desk drafts a plan that names only real pending transfers, and a planner still decides.
9. **An AI assistant can help too.** Through the MCP server, an assistant reads the plan and asks questions or proposes actions. The MCP server holds no data; every call goes through the API and its rules.

## Boundaries that matter

- **The browser never sees Databricks.** It gets stores, products and moves, never tables, queries or credentials.
- **The app runs as its own service principal**, with read access to the tables and write access only to `transfer_recommendations` and `transfer_audit`.
- **Free-form answers never run.** Nothing that Ask, the storm desk or an AI assistant returns is executed by the app.
- **Sample data is labelled.** Until real feeds replace the sample tables, the app shows a "Sample data" label.

## Current state

The daily job, the tables, the forecaster and the Ask space are built and run in the Databricks workspace. The app runs locally against the workspace. Hosting it as a Databricks App is defined and deploys with one command, but the app has not been switched on there yet, and real sales, stock and weather feeds are not connected yet. See the [runbook](runbook.md) and the [go-live checklist](go-live.md).
