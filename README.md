# StormSense

StormSense is a weather-aware inventory planning app for home improvement retail. It turns a seven-day weather outlook and store inventory into a clear daily plan: spot stores at risk of running low, see where surplus stock can help, and review suggested transfers before the weather hits.

The app supports the full planner workflow from a desktop or phone. The screenshots below were captured from the running frontend with the local sample-data API; they are saved in this repository under [`docs/screenshots/`](docs/screenshots/).

## Planner Workflow

1. **Start with Today.** See urgent transfers, stores at risk, the next weather alert, and a direct link to the recommended next action.

	![StormSense Today dashboard on desktop](docs/screenshots/app-today-desktop.png)

2. **Review transfer recommendations.** Recommendations are grouped into urgent and this-week lists. Each one explains the weather and demand behind the move, the quantity and route, estimated sales protected, confidence, the receiving store's low-stock day, and a link to its forecast.

	![Transfer recommendations grouped by urgency](docs/screenshots/app-transfers-desktop.png)

3. **Check the destination forecast.** Choose a store to inspect its week of weather, expected daily product demand, expected sales range, stock on hand and on the way, and any forecast low-stock dates. Transfer links open the destination store directly.

	![Store forecast with weekly weather and product demand](docs/screenshots/app-store-forecast-desktop.png)

4. **Make a guarded decision.** Planners can select one or many transfers. Approval asks for confirmation and accepts an optional note; rejection requires a reason. The app removes decided transfers from the pending list and reports the outcome. Viewers can inspect recommendations but cannot approve or reject them.

	![Transfer approval confirmation dialog](docs/screenshots/app-transfer-approval-dialog.png)

	![Successful transfer decision](docs/screenshots/app-transfers-approved.png)

5. **Keep an audit trail.** History records each approved or rejected transfer, the person who decided it, when it happened, and any note or rejection reason.

	![Transfer decision history](docs/screenshots/app-history-desktop.png)

6. **Ask a question in plain language.** The Ask page offers suggested questions and accepts questions about stores, products, and transfers. Answers can include a concise explanation and a supporting table. The screenshot shows the idle page; no Ask query was run for this README.

	![Ask page with suggested questions and input](docs/screenshots/app-ask-idle-desktop.png)

### Mobile Screens

Navigation moves to a five-item bottom bar on smaller screens, while transfer selection keeps the bulk actions within reach.

| Today | Transfers with a selection |
|---|---|
| ![Today on mobile](docs/screenshots/app-today-mobile.png) | ![Mobile transfers with bulk actions](docs/screenshots/app-transfers-mobile-selected.png) |

## Features

- **Weather-aware demand planning:** seven-day product forecasts respond to local weather and show expected units by day, a likely range, current and incoming stock, and when a product may run low.
- **Actionable transfer recommendations:** urgent and upcoming moves include route, quantity, rationale, distance, confidence, and estimated sales protected.
- **Bulk approvals and rejections:** planners can decide on multiple transfers at once, add an optional approval note, or provide a required rejection reason.
- **Role-based access:** planners can decide; viewers have read-only access. Decisions are protected by server-side checks, including when another planner has already handled a transfer.
- **Decision history:** approved and rejected recommendations remain available with actor, timestamp, and notes.
- **Plain-language Ask:** questions about stores, products, and transfers can return an answer with a supporting table.
- **Responsive and accessible UI:** desktop sidebar and mobile bottom navigation, keyboard support, visible focus, and accessible page and control labels.

## Run Locally

Requirements: Python 3.12 with [uv](https://docs.astral.sh/uv/) and Node.js 22.

```bash
make setup       # Create the Python environment and install web dependencies
make dev-sample  # Run the API and frontend using sample data
make test        # Run the Python and frontend unit tests
make e2e         # Build the app and run browser tests
```

The frontend is available at <http://localhost:5173>; the API is at <http://localhost:8000>. `make dev` uses sample data unless a local backend configuration selects a workspace. `make dev-sample` always uses fixtures, with no Databricks workspace or credits required. The fixtures are generated from the same shared planning code used by the data pipeline.

The end-to-end tests cover the approval-to-history workflow, concurrent decisions, viewer permissions, store forecasts, Ask responses, accessibility, keyboard navigation, and security headers.

## Run on Databricks

```bash
databricks auth login --host https://<your-workspace>.cloud.databricks.com --profile stormsense
make deploy
```

Deployment creates the schema and tables, trains and registers the forecaster, schedules the daily 6:00 AM job, creates the Ask space, and deploys the app from code. See the [runbook](docs/runbook.md) and [go-live checklist](docs/go-live.md).

## Repository Map

| Path | Purpose |
|---|---|
| [`frontend/`](frontend/) | React and TypeScript planner app: Today, Transfers, Stores, Ask, and History. |
| [`backend/`](backend/) | FastAPI application, identity and role checks, decision endpoints, audit history, and deployment definition. |
| [`databricks/`](databricks/) | Shared forecasting and planning code, notebooks, tables, and scheduled job resources. |
| [`infra/`](infra/) | Workspace deployment script, Docker configuration, and environment examples. |
| [`docs/`](docs/) | [System design](docs/system-design.md), [forecasting method](docs/forecasting.md), [runbook](docs/runbook.md), [verification guide](docs/how-to-verify.md), [data dictionary](docs/data-dictionary.md), and [demo script](docs/demo-script.md). |
| [`docs/screenshots/`](docs/screenshots/) | Saved product screenshots used in this README. |
| `src/`, root `index.html` | Public marketing site, separate from the planner app in `frontend/`. |

## Public Site

The repository-root landing page is deployed to GitHub Pages by `.github/workflows/deploy.yml`. That workflow also publishes the interactive architecture diagrams from `docs/architecture` under `/architecture/`.

- Site: <https://workatustadarshajay.github.io/STORMSENSE/>
- Architecture diagrams: <https://workatustadarshajay.github.io/STORMSENSE/architecture/>
- Rebuild the diagrams from `docs/architecture/src` with `make architecture`.

The site includes an animated Three.js radar globe, a scroll-driven weather-to-transfer story, a transfer approval interaction, and an ROI estimator with editable assumptions. It is responsive, supports system dark mode and reduced motion, and deploys to GitHub Pages on pushes to `main` or a manual workflow run.

Run the public site locally with Node.js 20 or later and npm:

```bash
npm ci
npm run dev
```

To build and preview it:

```bash
npm run build
npm run preview
```

For the first deployment, set **Settings > Pages** in the GitHub repository to use **GitHub Actions**. The workflow configures the repository subpath for project Pages URLs.

## License

This project is licensed under the MIT License. See [LICENSE](LICENSE).