# StormSense

Weather-aware inventory planning for home improvement retail. Every morning StormSense answers one question: **given the weather coming this week, which stores will run short, which have too much, and what should move where?** Planners approve the moves from a phone or laptop in a couple of minutes.

| Folder | What it holds |
|---|---|
| [`databricks/`](databricks) | The data and forecasting side: shared pipeline code, numbered notebooks, the daily job, the Ask space. Everything is created from code. |
| [`backend/`](backend) | The API (FastAPI): sign-in identity, roles, guarded approvals, audit trail, plain-language responses. Also the app's deployment definition. |
| [`frontend/`](frontend) | The web app (React, TypeScript, Tailwind): Today, Transfers, Store forecast, Ask, History. |
| [`infra/`](infra) | `deploy.sh` (creates everything in the workspace), Docker, environment example. |
| [`docs/`](docs) | [Architecture](docs/architecture.md), [forecasting method](docs/forecasting.md), [runbook](docs/runbook.md), [go-live checklist](docs/go-live.md), [how to verify](docs/how-to-verify.md), [data dictionary](docs/data-dictionary.md), [demo script](docs/demo-script.md). |
| `src/`, `index.html` | The public marketing page, deployed to GitHub Pages (see the end of this file). |

## Run it on your machine (no Databricks needed)

Requirements: Python 3.12 (with [uv](https://docs.astral.sh/uv/)) and Node.js 22.

```bash
make setup     # Python environment and web dependencies
make dev       # API on :8000, web app on http://localhost:5173, on sample data
make test      # library, API and web tests
make e2e       # browser tests against the built app
```

Sample mode serves realistic data built by the same code as the real tables, so the app works fully with no workspace and no credits.

## Run it on Databricks

```bash
databricks auth login --host https://<your-workspace>.cloud.databricks.com --profile stormsense
make deploy
```

This creates the schema and tables, trains and registers the forecaster, schedules the 6:00 AM job, creates the Ask space and deploys the app, all from code. See the [runbook](docs/runbook.md).

---

## Marketing page

The landing page that introduces StormSense lives at the repository root and is deployed to GitHub Pages by `.github/workflows/deploy.yml`.

### Features

- Animated Three.js radar globe in the hero
- Scroll-driven, three-step weather-to-transfer story
- Transfer approval interaction
- Interactive ROI estimate with editable assumptions
- Responsive layout, system dark mode, and reduced-motion support
- GitHub Actions deployment to GitHub Pages

### Run locally

Requirements: Node.js 20 or later and npm.

```bash
npm ci
npm run dev
```

Vite prints the local URL after the development server starts. To create and preview a production build:

```bash
npm run build
npm run preview
```

### Deploy

The workflow in `.github/workflows/deploy.yml` builds and deploys the site to GitHub Pages whenever code is pushed to `main`. It also supports a manual run from the Actions tab.

For the first deployment, open **Settings → Pages** in the GitHub repository and set the build and deployment source to **GitHub Actions**. The workflow automatically builds with the repository subpath, so project Pages URLs work without a manual Vite configuration change.

After deployment, the site is available at:

<https://workatustadarshajay.github.io/STORMSENSE/>

### Project structure

```text
.
├── .github/workflows/deploy.yml
├── docs/screenshots/       # README screen previews
├── src/main.jsx            # React page and Three.js scene
├── src/styles.css          # Responsive styles and motion
├── index.html
└── vite.config.js
```

### Technology

React 18, Vite, Three.js, React Three Fiber, GSAP ScrollTrigger, Framer Motion, and Lucide icons.

### License

This project is licensed under the MIT License. See [LICENSE](LICENSE).