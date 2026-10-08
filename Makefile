# Common commands. Run `make help`.
PY      := .venv/bin/python
PROFILE ?= stormsense

# Behind a company proxy, Python needs the system certificate store to reach Databricks (the CLI already uses it).
ifneq ($(wildcard /etc/ssl/certs/ca-certificates.crt),)
export REQUESTS_CA_BUNDLE ?= /etc/ssl/certs/ca-certificates.crt
export SSL_CERT_FILE ?= /etc/ssl/certs/ca-certificates.crt
endif

.PHONY: help setup dev dev-sample dev-api dev-web test lint e2e types fixtures docs architecture build-app smoke deploy deploy-data deploy-app pause resume

help:  ## Show this list
	@grep -E '^[a-z-]+:.*##' $(MAKEFILE_LIST) | awk -F':.*## ' '{printf "  %-12s %s\n", $$1, $$2}'

setup:  ## Install everything needed to build and test locally
	uv venv --python 3.12 .venv
	uv pip install --python $(PY) -r backend/requirements-dev.txt -r databricks/requirements-dev.txt
	cd frontend && npm ci

dev:  ## Run the app: API on :8000, web app on :5173. Real data if backend/.env exists, otherwise sample data
	$(MAKE) -j2 dev-api dev-web

dev-sample:  ## Same, but always on sample data (no workspace needed)
	STORMSENSE_MODE=mock STORMSENSE_DEV_USER_EMAIL=ava.planner@stormsense.test $(MAKE) -j2 dev-api dev-web

dev-api:
	cd backend && ../$(PY) -m uvicorn app.main:create_default_app --factory --reload --port 8000

dev-web:
	cd frontend && npm run dev

test:  ## Library, API and web tests
	$(PY) -m pytest databricks/tests backend -q
	cd frontend && npm test

lint:  ## Lint and type-check everything
	$(PY) -m ruff check databricks backend
	cd frontend && npm run lint && npm run typecheck

e2e: build-app  ## Browser tests against the built app
	cd frontend && npx playwright test

types:  ## Regenerate the web app's API types from the backend
	cd backend && ../$(PY) scripts/export_openapi.py ../frontend/openapi.json
	cd frontend && npm run types

fixtures:  ## Regenerate the sample data the app uses without a workspace
	$(PY) databricks/scripts/make_fixtures.py

docs:  ## Regenerate the data dictionary
	$(PY) -c "import sys; sys.path.insert(0, 'databricks'); from stormsense_core.tables import data_dictionary; print(data_dictionary())" > docs/data-dictionary.md

architecture:  ## Regenerate the architecture website's diagrams from docs/architecture/src (set ARCHIFY_CHROME to a Chrome binary)
	@for spec in "architecture architecture-system system" "dataflow dataflow-daily-pipeline daily-pipeline" \
	  "sequence sequence-approve-transfer approve-transfer" "lifecycle lifecycle-transfer transfer-lifecycle" "workflow workflow-deploy deploy"; do \
	  set -- $$spec; echo "== $$3"; \
	  node .agents/skills/archify/bin/archify.mjs finalize $$1 docs/architecture/src/$$2.json docs/architecture/$$3.html --quality showcase || exit 1; \
	done

build-app:  ## Build the web app into backend/static
	cd frontend && npm run build
	rm -rf backend/static && cp -r frontend/dist backend/static

smoke:  ## Check a real workspace end to end (needs WAREHOUSE_ID and SPACE_ID)
	cd backend && ../$(PY) scripts/smoke.py --profile $(PROFILE) --warehouse-id $(WAREHOUSE_ID) --space-id $(SPACE_ID)

deploy:  ## Create everything in the workspace: data, forecaster, daily job, Ask space, app
	PROFILE=$(PROFILE) PY=$(PY) infra/deploy.sh

deploy-data:  ## Only the data and forecasting side
	cd databricks && databricks bundle deploy --profile $(PROFILE)

deploy-app: build-app  ## Only the app (needs WAREHOUSE_ID and SPACE_ID)
	cd backend && databricks bundle deploy --profile $(PROFILE) --var warehouse_id=$(WAREHOUSE_ID) --var genie_space_id=$(SPACE_ID)
	cd backend && databricks bundle run stormsense --profile $(PROFILE)

pause:  ## Stop the 6:00 AM schedule
	cd databricks && databricks bundle deploy --profile $(PROFILE) --var schedule_status=PAUSED

resume:  ## Start the 6:00 AM schedule
	cd databricks && databricks bundle deploy --profile $(PROFILE) --var schedule_status=UNPAUSED
