# API reference

Every endpoint the web app and the MCP server call. This page is generated from the API's own description (`frontend/openapi.json`, version 1.0.0), so it matches the code.

!!! note "Who can call what"
    Reading is open to anyone who can sign in. Approving and rejecting need a planner or admin account. Storm desk, Ask and the what-if are rate-limited per person. Every write needs the `X-Requested-With: stormsense` header.

Errors come back as `{"detail": {"code": "...", "message": "..."}}` with a plain-language message.

### `GET /api/analysis/charts`

Analysis Charts

Demand, stock, shortages, transfers and protected sales, for the chosen data source.

**Response**

Returns object.

### `POST /api/ask`

Ask

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `question` | string | yes | min length 3; max length 500 |

**Response**

Returns AskResponse.

| Field | Type | Notes |
|---|---|---|
| `answer` | string |  |
| `answered` | boolean |  |
| `table` | AskTable (optional) |  |

### `GET /api/backtest`

Backtest

Past storms replayed with what really sold: the sales lost, and how much nearby stock could have covered.

An upper bound, not a forecast.

**Response**

Returns list of BacktestStorm.

### `GET /api/briefing`

Briefing

The morning briefing: a few plain sentences from today's figures, for the chosen data source.

**Response**

Returns Briefing.

| Field | Type | Notes |
|---|---|---|
| `headline` | string |  |
| `lines` | list of string |  |

### `POST /api/demo/alert`

Demo Alert

Starts the demo email job. Databricks sends the email to the alert address. Planners only.

**Response**

Returns DemoAlertResult.

| Field | Type | Notes |
|---|---|---|
| `message` | string |  |
| `started` | boolean |  |

### `GET /api/health`

Health

Liveness. With ?deep=true it also checks the data connection (this wakes the warehouse, so keep probes sparse).

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `deep` | query | boolean | no | default `false` |

**Response**

Returns Health.

| Field | Type | Notes |
|---|---|---|
| `mode` | string |  |
| `status` | one of `ok`, `starting`, `unavailable` |  |
| `warehouse` | one of `ready`, `starting`, `unavailable`, `not_checked` |  |

### `GET /api/history`

History

**Response**

Returns list of Transfer.

### `GET /api/impact`

Impact

What the plan is worth: protected sales, estimated profit and carbon, the decisions made, and the timeline of updates.

**Response**

Returns Impact.

| Field | Type | Notes |
|---|---|---|
| `as_of` | string (optional) |  |
| `assumptions` | list of string |  |
| `changes` | ChangeSince |  |
| `headline` | ImpactHeadline |  |
| `source` | string |  |
| `timeline` | list of TimelineEvent |  |

### `GET /api/ingest/analysis`

Analysis

A plain analysis of your uploaded data. Needs the stores, products, sales and stock files.

**Response**

Returns Analysis.

| Field | Type | Notes |
|---|---|---|
| `as_of` | string |  |
| `by_store` | list of AnalysisStore |  |
| `items` | list of AnalysisItem | The short and watch items, most urgent first |
| `pairs` | integer |  |
| `products` | integer |  |
| `sales_value_usd` | number |  |
| `short` | integer |  |
| `sold_units` | integer |  |
| `stock_value_usd` | number |  |
| `stores` | integer |  |
| `watch` | integer |  |
| `window_days` | integer |  |

### `GET /api/ingest/charts`

Upload Charts Route

Chart data about your uploads: sales and stock by day, cover by store, status counts, and what was loaded.

**Response**

Returns object.

### `GET /api/ingest/checks`

Upload Checks

**Response**

Returns ChecksResult.

| Field | Type | Notes |
|---|---|---|
| `sentences` | list of string |  |

### `POST /api/ingest/demo/load`

Load Demo

Loads the four sample workbooks in order, then builds the plan. One click for a demo.

**Response**

Returns object.

### `POST /api/ingest/drop/scan`

Scan Drop Now

Loads any files waiting in the drop folder now, instead of waiting for the next check.

**Response**

Returns DropResult.

| Field | Type | Notes |
|---|---|---|
| `folder` | string |  |
| `loaded` | list of string |  |

### `GET /api/ingest/economics`

Get Economics

**Response**

Returns EconomicsBody.

| Field | Type | Notes |
|---|---|---|
| `margin_pct` | number | Share of sales that is profit, in percent; ≥ 0.0; ≤ 100.0 |
| `truck_cost_per_mile` | number | What one truck trip costs per mile, in dollars; ≥ 0.0; ≤ 20.0 |

### `PUT /api/ingest/economics`

Set Economics

Truck cost per mile and product margin, used for the estimated profit of the plan.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `margin_pct` | number | yes | Share of sales that is profit, in percent; ≥ 0.0; ≤ 100.0 |
| `truck_cost_per_mile` | number | yes | What one truck trip costs per mile, in dollars; ≥ 0.0; ≤ 20.0 |

**Response**

Returns EconomicsBody.

| Field | Type | Notes |
|---|---|---|
| `margin_pct` | number | Share of sales that is profit, in percent; ≥ 0.0; ≤ 100.0 |
| `truck_cost_per_mile` | number | What one truck trip costs per mile, in dollars; ≥ 0.0; ≤ 20.0 |

### `GET /api/ingest/feeds`

Feeds

**Response**

Returns list of FeedInfo.

### `DELETE /api/ingest/feeds/{feed}`

Clear

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `feed` | path | string | yes |  |

**Response**

Returns object.

### `GET /api/ingest/feeds/{feed}/preview`

Preview

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `feed` | path | string | yes |  |
| `limit` | query | integer | no | default `20` |

**Response**

Returns list of object.

### `POST /api/ingest/feeds/{feed}/rows`

Rows In

Send rows from another system as JSON. Same checks as a file upload.

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `feed` | path | string | yes |  |

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `mapping` | object (optional) | no |  |
| `rows` | list of object | yes | at most 5000 items |

**Response**

Returns UploadResult.

| Field | Type | Notes |
|---|---|---|
| `feed` | string |  |
| `ignored_columns` | list of string |  |
| `kept` | integer |  |
| `message` | string |  |
| `missing_columns` | list of string |  |
| `refusals` | list of Refusal | The first 20 refused rows, with the line number and the reason |
| `refused` | integer |  |

### `GET /api/ingest/feeds/{feed}/template.xlsx`

Template Xlsx

An Excel template. Store and product codes are dropdowns, filled from the stores and products you uploaded.

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `feed` | path | string | yes |  |

### `POST /api/ingest/feeds/{feed}/upload`

Upload

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `feed` | path | string | yes |  |

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `csv` | string (optional) | no | The whole CSV file as text, with the column names on the first line |
| `mapping` | object (optional) | no | Your column name for each StormSense column, if the names differ |
| `xlsx_base64` | string (optional) | no | An Excel file (.xlsx), base64 encoded. Columns are matched by name |

**Response**

Returns UploadResult.

| Field | Type | Notes |
|---|---|---|
| `feed` | string |  |
| `ignored_columns` | list of string |  |
| `kept` | integer |  |
| `message` | string |  |
| `missing_columns` | list of string |  |
| `refusals` | list of Refusal | The first 20 refused rows, with the line number and the reason |
| `refused` | integer |  |

### `POST /api/ingest/plan`

Build Plan

Builds the plan from your uploads. The planner's screens can then use them as "Your uploads".

**Response**

Returns PlanStatus.

| Field | Type | Notes |
|---|---|---|
| `as_of` | string (optional) |  |
| `net_benefit` | object (optional) |  |
| `ready` | boolean |  |
| `summary` | object (optional) |  |

### `GET /api/ingest/plan/status`

Plan Status

**Response**

Returns PlanStatus.

| Field | Type | Notes |
|---|---|---|
| `as_of` | string (optional) |  |
| `net_benefit` | object (optional) |  |
| `ready` | boolean |  |
| `summary` | object (optional) |  |

### `GET /api/inventory`

Inventory

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `status` | query | one of `RUNNING_LOW`, `EXTRA` (optional) | no |  |

**Response**

Returns list of InventoryItem.

### `GET /api/markdowns`

Markdowns

Surplus stock that would not sell in time at full price, with a discount that adds cash. Suggestions only: nothing changes.

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `weather` | query | one of `live`, `demo` | no | default `"live"` |

**Response**

Returns list of MarkdownSuggestion.

### `POST /api/markdowns/decision`

Decide Markdown

A planner approves or rejects a markdown suggestion. Records the decision; nothing changes in the stores.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `decision` | one of `APPROVED`, `REJECTED` | yes |  |
| `product_id` | string | yes | matches `"^P\\d{2}$"` |
| `store_id` | string | yes | matches `"^S\\d{2}$"` |

**Response**

Returns MarkdownSuggestion.

| Field | Type | Notes |
|---|---|---|
| `assumption` | string | How the estimate was made, so it can be checked |
| `clears_all` | boolean |  |
| `current_price` | number |  |
| `decided_at` | string (optional) |  |
| `decided_by` | string (optional) |  |
| `decision` | string | pending, approved or rejected by a planner; default `"pending"` |
| `discount_pct` | integer | Suggested discount, 10 to 40 percent; ≥ 10.0; ≤ 40.0 |
| `extra_cash_usd` | number | Cash expected over holding the stock at full price, an estimate |
| `new_price` | number |  |
| `note` | string |  |
| `product` | ProductRef |  |
| `spare_units` | integer | Stock the store will not need in the week ahead |
| `store` | Ref |  |
| `units_cleared` | integer | Units expected to sell in the clearance window at this discount |

### `GET /api/me`

Me

**Response**

Returns Me.

| Field | Type | Notes |
|---|---|---|
| `can_approve` | boolean |  |
| `data_label` | string (optional) | Set to 'sample' while the app shows sample data |
| `email` | string |  |
| `name` | string |  |
| `role` | one of `viewer`, `planner`, `admin` |  |

### `GET /api/overview`

Overview

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `weather` | query | one of `live`, `demo` | no | default `"live"` |

**Response**

Returns Overview.

| Field | Type | Notes |
|---|---|---|
| `alerts` | list of WeatherAlert |  |
| `as_of` | string (optional) |  |
| `next_action` | NextAction |  |
| `next_alert` | WeatherAlert (optional) |  |
| `pending_transfers` | integer |  |
| `stores_at_risk` | integer |  |
| `urgent_transfers` | integer |  |
| `weather_source` | one of `live`, `demo` | demo means a demo storm is placed on the weather screens; default `"live"` |

### `GET /api/stores`

Stores

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `weather` | query | one of `live`, `demo` | no | default `"live"` |

**Response**

Returns list of StoreSummary.

### `GET /api/stores/{store_id}/forecast`

Store Forecast

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `store_id` | path | string | yes | matches `"^S\\d{2}$"` |
| `weather` | query | one of `live`, `demo` | no | default `"live"` |

**Response**

Returns StoreForecast.

| Field | Type | Notes |
|---|---|---|
| `as_of` | string (optional) |  |
| `products` | list of ProductForecast |  |
| `store` | StoreSummary |  |
| `weather` | list of WeatherDay |  |
| `weather_source` | one of `live`, `demo` | demo means a demo storm is placed on this forecast's weather; default `"live"` |

### `POST /api/storm-desk`

Storm Desk

Plans from the live data. Read-only: it can suggest moves but never approves or changes anything.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `goal` | string | yes | min length 3; max length 500 |

**Response**

Returns StormDeskPlan.

| Field | Type | Notes |
|---|---|---|
| `answered` | boolean |  |
| `debate` | list of DebateTurn | How the three roles arrived at the plan |
| `message` | string (optional) |  |
| `plan` | list of string | The plan, one sentence per item |
| `steps` | list of DeskStep | What storm desk checked, in order |
| `transfers` | list of Transfer | Pending transfers the plan refers to |

### `GET /api/transfers`

Transfers

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `status` | query | one of `PENDING`, `APPROVED`, `REJECTED` (optional) | no |  |
| `urgency` | query | one of `URGENT`, `NORMAL` (optional) | no |  |

**Response**

Returns list of Transfer.

### `POST /api/transfers/approve`

Approve

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `ids` | list of string | yes | at least 1 items; at most 50 items |
| `note` | string (optional) | no |  |

**Response**

Returns DecisionResult.

| Field | Type | Notes |
|---|---|---|
| `action` | one of `APPROVED`, `REJECTED` |  |
| `changed` | list of string |  |
| `message` | string |  |
| `skipped` | list of string |  |

### `GET /api/transfers/export`

Export Transfers

The plan as a spreadsheet (CSV). Read-only. Open it in a spreadsheet, or print it to PDF from the browser.

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `status` | query | one of `PENDING`, `APPROVED`, `REJECTED` (optional) | no |  |

### `POST /api/transfers/reject`

Reject

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `ids` | list of string | yes | at least 1 items; at most 50 items |
| `reason` | string | yes | min length 3; max length 280 |
| `reason_code` | one of `TRUCK_UNAVAILABLE`, `STORE_CLOSED`, `ALREADY_COVERED`, `ROUTE_TOO_SLOW`, `OTHER` (optional) | no | Structured reason; the daily run learns from it |

**Response**

Returns DecisionResult.

| Field | Type | Notes |
|---|---|---|
| `action` | one of `APPROVED`, `REJECTED` |  |
| `changed` | list of string |  |
| `message` | string |  |
| `skipped` | list of string |  |

### `GET /api/transfers/{transfer_id}`

Transfer

**Parameters**

| Name | In | Type | Required | Notes |
|---|---|---|---|---|
| `transfer_id` | path | string | yes | matches `"^TR-[A-Z0-9]{10}$"` |

**Response**

Returns Transfer.

| Field | Type | Notes |
|---|---|---|
| `co2_kg` | number | Estimated kg CO2e for the move. See carbon.py for the assumptions.; default `0` |
| `confidence` | one of `High`, `Medium`, `Low` |  |
| `created_at` | string (optional) |  |
| `decided_at` | string (optional) |  |
| `decided_by` | string (optional) |  |
| `distance_miles` | integer |  |
| `from_store` | Ref |  |
| `headline` | string |  |
| `id` | string |  |
| `note` | string (optional) |  |
| `product` | ProductRef |  |
| `qty` | integer |  |
| `reason` | string |  |
| `runs_low_day` | string (optional) |  |
| `sales_protected_usd` | number |  |
| `status` | one of `PENDING`, `APPROVED`, `REJECTED` |  |
| `to_store` | Ref |  |
| `urgency` | one of `URGENT`, `NORMAL` |  |

### `POST /api/what-if`

What If

Simulates a storm and what it would cost. Read-only: it changes no data and approves nothing.

**Request body**

| Field | Type | Required | Notes |
|---|---|---|---|
| `days` | integer | yes | How many days the storm lasts; ≥ 1.0; ≤ 4.0 |
| `region` | one of `Florida`, `Texas`, `California` (optional) | no |  |
| `start_day` | integer | yes | 0 means tomorrow; ≥ 0.0; ≤ 6.0 |
| `strength` | integer | yes | How strong the storm is, 0 to 100; ≥ 0.0; ≤ 100.0 |

**Response**

Returns WhatIfResult.

| Field | Type | Notes |
|---|---|---|
| `answered` | boolean |  |
| `extra_demand_units` | integer | default `0` |
| `extra_lost_usd` | number | default `0.0` |
| `message` | string (optional) |  |
| `normal_units` | integer | default `0` |
| `plan_change` | PlanChange (optional) |  |
| `rows` | list of WhatIfRow |  |
| `sentence` | string (optional) |  |
| `stock_to_move_units` | integer | default `0` |
| `storm_units` | integer | default `0` |
| `window` | string (optional) |  |
