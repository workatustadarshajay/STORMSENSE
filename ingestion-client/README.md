# StormSense ingestion client

A small front end for connecting your data to StormSense. It uses the backend's data-ingest routes, so there is one backend and two front ends: the planner app, and this client.

- Upload the four files (stores, products, daily sales, daily stock) as CSV, with column matching and row-by-row checks.
- Other systems can send the same rows as JSON to the same routes.
- An AI assistant can connect through the MCP server instead.

Uploads are off unless the server has `STORMSENSE_INGEST_ENABLED=1`.

## Run

```bash
cd ingestion-client
npm install
npm run dev          # http://localhost:5174, forwards /api to the backend on port 8000
npm test
npm run build        # writes dist/, which the backend serves at /ingest/
```
