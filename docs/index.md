---
hide:
  - navigation
---

# StormSense

**Which stores will run short this week, which have spare stock, and what should move where?**

StormSense reads the weather coming up, forecasts demand for each store and product, and proposes stock transfers between stores before a storm arrives. A planner reviews each move and approves or rejects it. Nothing moves until a person says so.

<div class="grid cards" markdown>

- :material-weather-hurricane: **Plan for the weather**

    The forecast uses the next few days of weather, so generators, plywood and pumps are moved before a storm, not after.

- :material-truck-delivery: **Decide in minutes**

    Urgent moves come first, with the reason, the sales they protect, and how sure the forecast is.

- :material-shield-check: **Every decision is recorded**

    Who approved or rejected what, when, and why, is kept in an audit trail.

- :material-connection: **Works with other tools**

    An MCP server lets an AI assistant or another app read the plan and act on it, under the same rules.

</div>

## Start here

| If you are... | Read |
|---|---|
| A store planner | [Planner guide](planner-guide.md), then the [five-minute demo](demo-script.md) |
| Setting it up or running it | [Run it on your machine](running-locally.md) and the [runbook](runbook.md) |
| Building on it or connecting to it | [MCP server and client](integrations/mcp.md) and the [API reference](api-reference.md) |
| Reviewing the design | [System design](system-design.md), the [diagrams](https://workatustadarshajay.github.io/STORMSENSE/architecture/), [forecasting method](forecasting.md) and the [data dictionary](data-dictionary.md) |
| Checking the build | [How to check it works](how-to-verify.md) |

## What is built, and what is still to do

| Area | Status |
|---|---|
| Forecast, transfer plan, approvals and audit trail | Built and checked on the Databricks workspace |
| Daily job with live US National Weather Service forecasts | Built and checked end to end |
| Data-quality checks, dashboard and cost view | Built; the cost view fills in once billing data arrives |
| What-if storm simulator | Built and checked against the live forecaster |
| Feedback loop from rejected moves | Built and checked; learning only ranks routes lower, never removes moves |
| Storm desk (three-agent crew) | Built and checked live |
| MCP server and client | Built and tested against sample data |
| Databricks App deployment | Blocked by the company web filter; the app runs locally against the workspace |

!!! info "Sample data"
    The sales and stock figures are generated sample data. The app shows a **Sample data** label until real store feeds are connected. The weather is live.
