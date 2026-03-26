# PRD: MRP Taiwan Inventory Forecasting — AI-Powered Control Tower
**Project:** BYU IS Capstone — Mountain Racing Products (MRP)
**Author:** Preston Vance
**Version:** 0.1 (Draft)
**Last Updated:** 2026-03-16
**Status:** Draft — Pending Rich's answers and sample MieTrak CSVs

---

## 1. Background & Problem Statement

Mountain Racing Products (MRP) is a small bicycle parts manufacturer operating two divisions: a US retail/assembly operation and a manufacturing plant in Taiwan. Their ERP (MieTrak by MIE Solutions) does not support three critical planning functions:

1. **Time-phased Taiwan inventory planning** — tracking what week inventory runs out against both Taiwan orders and US-bound shipments simultaneously
2. **Sea vs. air freight decisions** — determining when air freight is necessary to protect US customer orders
3. **Customer forecast integration** — ingesting CSV demand forecasts from OEM customers (e.g., Giant) that MieTrak cannot consume natively

To compensate, their supply chain manager (Rich) maintains a complex multi-tab Excel workbook ("Inventory B") that has reached Version 9 and is showing fragility at its current scale. The workbook is updated manually 1–3 times per week via copy/paste from MieTrak CSV exports, with additional manual column insertions for each sea/air release event.

This project replaces the brittle spreadsheet workflow with an automated Microsoft Fabric data platform and adds an AI layer for exception detection, plain-English alerts, and sea vs. air shipping recommendations.

---

## 2. Goals

### Primary Goals (MVP — must ship)
- [ ] Automate ingestion of MieTrak CSV exports into a Fabric Lakehouse
- [ ] Replicate the core Inventory B ordering algorithm in SQL/notebook logic
- [ ] Detect and surface parts projected to go negative before the next sea shipment
- [ ] Generate a PO Needs list (parts where projected balance goes negative) automatically
- [ ] Power BI dashboard showing time-phased supply vs. demand by part

### Secondary Goals (stretch — ship if time allows)
- [ ] Sea vs. air recommendation engine per part, using the WOH logic from the Release tab
- [ ] AI-generated daily digest email/Teams message summarizing top risks in plain English
- [ ] Forecast anomaly alert when a customer forecast upload changes demand by >25%

### Non-Goals (explicitly out of scope for this project)
- US order management / order tracking dashboard (separate workbook, future phase)
- Direct MieTrak API integration (no API access; CSV export only)
- Full BOM explosion / MRP calculation engine
- Replacing MieTrak as the ERP system
- Customer-facing chatbot or marketing AI features

---

## 3. Users & Roles

| User | Role in System | Primary Need |
|---|---|---|
| Rich (Supply Chain Manager) | Primary operator | Replace weekly spreadsheet update process; see PO Needs and sea/air recommendations automatically |
| Tim Fry (Co-founder) | Executive | Quick answer to "what's at risk today?" without opening spreadsheets |
| Christy Fry (Co-founder/IT) | Admin + data owner | Understand and approve the system; manage MieTrak exports |
| Cindy | Release approver | Receive release Excel file; currently a manual email step |
| Preston (Developer) | Builder | Build, document, and hand off the system |

---

## 4. Data Sources

### 4.1 MieTrak ERP (Primary — Taiwan orders, work orders, open POs)
- **Access method:** Manual report export to CSV or Excel, triggered by Rich or Christy
- **Delivery:** Email to a shared mailbox (e.g., ai@mrpbike.com) or dropped into a SharePoint/OneDrive folder
- **Frequency:** 1–3x per week (daily when order urgency is high)
- **Key reports needed:**
  - Open Sales Orders (Taiwan division)
  - Open Sales Orders (US division)
  - Open Purchase Orders
  - Inventory on-hand by part/location
  - Work Orders / production status
- **Division split:** MieTrak has two divisions (US + Taiwan); exports should be separated or tagged by division

### 4.2 US On-Hand Inventory
- **Access method:** CSV/Excel export from MieTrak or other specified system (pending Rich confirmation)
- **Delivery:** Same shared mailbox or SharePoint folder
- **Frequency:** At minimum with each Inventory B refresh (1–3x/week)
- **Key data:** US warehouse on-hand quantities by part number

### 4.3 Customer Forecast Files (OEM demand)
- **Source:** Customers such as Giant provide periodic demand forecast CSVs
- **Format:** Customer-specific; may use customer part numbers (requires mapping to internal MRP part numbers)
- **Delivery:** Manually dropped into a designated SharePoint folder or emailed
- **Frequency:** Weekly or per customer schedule
- **Special case:** Giant has a dedicated forecast tab in Inventory B with separate handling

### 4.4 Manual Inputs (cannot be eliminated in MVP)
- **US OEM inventory (EOM paper count):** Still manually entered per the instructions screenshot; no digital source
- **Demand Factor:** A per-part multiplier for adjusting historical usage. Currently 1.00 for all parts in the cleaned dataset — pending confirmation from Rich on when/how this is adjusted
- **Pre-paid column:** Manually maintained to track items that have rolled into pre-paid status; must be updated on each release
- **"DO NOT REORDER" flags:** Manually annotated part descriptions — need to understand if this maps to a lifecycle status in MieTrak or is spreadsheet-only

---

## 5. Core Ordering Algorithm

The central calculation replicated from the spreadsheet's "Running Inventory" tab ordering algorithm note:

```
Months of Supply = 
  ( Stock On Hand 
  + Stock Inbound (POs) 
  + Pending Release Quantities 
  - (Monthly Avg Usage × Lead Time to Next Sea Release in months) )
  / Monthly Avg Usage
```

**Business rules:**
- Target value = months until the NEXT sea release arrives (e.g., if next sea is 4 weeks out, target = 1.0)
- If no US usage data exists for a part, the algorithm does not populate (null, not zero)
- Seasonal adjustment: the algorithm note says the result "changes unwantedly" when new releases are built — manual review is needed when a release is created
- The DEMAND FACTOR column is a multiplier on monthly average usage (default 1.00; adjustment conditions TBD)

---

## 6. Data Model

### 6.1 Lakehouse Layers

| Layer | Contents |
|---|---|
| **Bronze** | Raw landed files — MieTrak CSV, customer forecast CSV, manual exception inputs |
| **Silver** | Cleaned, standardized, deduplicated tables with consistent part keys and normalized dates |
| **Gold** | Business-ready fact and dimension tables; derived views for planning and exception logic |

### 6.2 Core Tables (Gold Layer)

#### Dimension Tables
```
dim_part
  part_id (internal MRP number, e.g. MR-03-084-K)
  description
  product_family
  product_line
  unit_of_measure
  make_buy_flag
  active_status  -- maps to "DO NOT REORDER" and lifecycle state
  default_supplier
  standard_lead_time_weeks
  moq
  unit_cost
  safety_stock_months
  demand_factor    -- multiplier on avg usage; default 1.00
  planning_notes   -- freetext (e.g. "WATCH REORDER", "MOVE TO US")

dim_customer
  customer_id
  customer_name
  customer_type    -- OEM, distributor, dealer, aftermarket
  oem_flag
  active

dim_supplier
  supplier_id
  supplier_name
  region           -- Taiwan, US, other
  lead_time_weeks
  active

dim_location
  location_id
  location_name
  location_type    -- US warehouse, Taiwan warehouse, in-transit-sea, in-transit-air
  country

dim_calendar
  date
  week_start
  half_month_bucket  -- M1A, M1B, M2A, M2B, etc.
  month
  quarter

dim_customer_part_map
  customer_id
  customer_part_number
  internal_part_id
  effective_start
  effective_end
  active
```

#### Fact Tables
```
fact_inventory_snapshot
  snapshot_date
  part_id
  location_id
  on_hand_qty
  committed_qty
  available_qty
  source_system    -- MieTrak

fact_sales_order_line
  order_line_id
  order_number
  customer_id
  part_id
  division         -- US or Taiwan
  order_date
  requested_ship_date
  promise_date
  ordered_qty
  open_qty
  status
  revenue_amount
  load_timestamp

fact_purchase_order_line
  po_line_id
  po_number
  supplier_id
  part_id
  destination_location_id
  order_date
  due_date
  ordered_qty
  received_qty
  open_qty
  unit_cost
  status
  load_timestamp

fact_forecast
  forecast_id
  customer_id
  part_id
  forecast_date
  planning_bucket     -- half-month bucket label
  forecast_qty
  forecast_version
  upload_date
  source_file

fact_release_event
  release_id
  release_date
  release_type        -- sea or air
  part_id
  qty_released
  destination         -- US
  estimated_arrival_date
  sea_shipment_number
  cost
  created_by

fact_exception
  exception_id
  exception_type
  object_type         -- part, order, PO
  object_key
  detected_at
  severity            -- critical, warning, info
  owner
  status              -- open, acknowledged, resolved
  recommended_action
  notes
  resolved_at
```

#### Derived Views
```
vw_projected_supply_demand
  -- Grain: part × location × half-month bucket
  -- Calculates: starting inventory + inbound POs + releases − TW orders − forecast demand
  -- Output: projected ending balance per bucket; projected stockout date

vw_part_criticality  (replaces PO Needs tab)
  -- Grain: part
  -- Calculates: months of supply using the ordering algorithm
  -- Flags: needs_reorder (true when projected balance < 0 before next sea)
  -- Output: ordered by urgency; feeds PO Needs report

vw_shipping_recommendation  (replaces Release tab logic)
  -- Grain: part × planned release event
  -- Calculates: WOH before sea arrives (goal: 0), WOH when sea arrives (goal: 4)
  -- Output: recommendation = no_action | release_to_sea | expedite_air | management_review
```

---

## 7. Features

### F-01: Automated CSV Ingestion Pipeline
**Priority:** P0 — required for all other features

A Fabric Data Factory pipeline that:
- Monitors a SharePoint folder or shared mailbox attachment drop
- Detects new CSV files by source type (MieTrak orders, MieTrak inventory, customer forecast)
- Validates schema and logs any column mismatches
- Lands raw files in the Bronze Lakehouse layer with a timestamp and source tag
- Triggers downstream Silver/Gold transformation notebooks on successful load

**Acceptance criteria:**
- Given a new MieTrak CSV in the designated folder, the pipeline runs within 15 minutes and the Gold layer tables are refreshed
- Failed loads surface an error in the Fabric monitoring dashboard and do not overwrite previous good data

---

### F-02: Supply/Demand Projection (Ordering Algorithm)
**Priority:** P0 — core business logic

A SQL/notebook transformation that:
- Implements the ordering algorithm from the Instructions doc (see Section 5)
- Calculates projected inventory balance per part per half-month bucket for the next 6 months
- Flags any part where the projected balance goes negative before the next sea release date
- Writes results to `vw_projected_supply_demand` and `vw_part_criticality`

**Acceptance criteria:**
- For a set of 10 test parts with known values from the current Inventory B spreadsheet, the Fabric calculation matches within ±5% of the spreadsheet output
- Parts with no US usage data return null (not zero) per the algorithm spec

---

### F-03: PO Needs Report
**Priority:** P0 — direct replacement for PO Needs tab

An automated output that:
- Lists all parts where the ordering algorithm flags a reorder need
- Excludes parts marked active_status = 'DO NOT REORDER' or with zero demand
- Includes: part number, description, recommended order quantity, urgency (weeks until stockout), and default supplier
- Exportable to Excel for Rich to submit to suppliers

**Acceptance criteria:**
- Output matches what the current PO Needs tab generates for the same input data
- Export produces a clean Excel file without blank rows (current manual step eliminated)

---

### F-04: Planner Dashboard (Power BI)
**Priority:** P1

A Power BI report with two focused pages:

**Page 1 — Parts at Risk**
- Table of parts flagged by `vw_part_criticality`, sorted by weeks until stockout
- Color coding: red (<2 weeks), yellow (2–4 weeks), green (>4 weeks)
- Filters: product family, supplier, customer

**Page 2 — Time-Phased Supply vs. Demand**
- Bar/waterfall chart showing projected balance per half-month bucket for a selected part
- Drill-down from part list to individual part view
- Shows: on-hand, incoming sea/air, committed TW orders, US allocations, and projected net

**Acceptance criteria:**
- Tim can answer "what parts are at risk this week?" within 60 seconds of opening the dashboard
- Dashboard refreshes automatically after each pipeline run

---

### F-05: Exception Alerts (Teams / Email)
**Priority:** P1

Fabric Activator rules or Power Automate flows that fire when:
- A part is projected to go negative within 14 days
- A PO is overdue and the part has active Taiwan demand
- A customer forecast upload changes demand by more than 25% week-over-week

Alert format (Teams message):
```
⚠️ MRP Inventory Alert
Part: MR-03-084-K (TR Skid Black)
Issue: Projected stockout in 9 days
Demand: 34.7 units/week | Supply: 300 on-hand + 0 inbound
Recommendation: Evaluate air shipment or pull from US stock
```

**Acceptance criteria:**
- At least one alert type is functional in the demo environment
- Alerts do not fire for parts flagged DO NOT REORDER

---

### F-06: AI Digest Agent (Stretch)
**Priority:** P2 — stretch goal

A daily automated summary generated by an LLM (Azure OpenAI / Fabric Copilot) that:
- Queries `fact_exception` and `vw_part_criticality` each morning
- Generates a 5–8 sentence plain-English summary of the top risks
- Sends via email or Teams to Tim and Rich

Example output:
> "Good morning. As of today, 4 parts are projected to run short before the next sea shipment arriving April 15. The most urgent is MR-03-119-CS (ProductA Steel CS), which is expected to go negative by April 3rd — 12 days from now. A purchase order has not yet been placed. The Giant forecast uploaded Monday increased demand for this part by 31% versus last week. Recommend Rich review and place a PO or authorize an air shipment this week."

**Acceptance criteria:**
- Output is factually grounded in the Fabric data (no hallucinated quantities)
- Summary is generated and delivered by 8:00 AM on each business day the pipeline runs

---

### F-07: Sea vs. Air Recommendation Engine (Stretch)
**Priority:** P2 — stretch goal

A derived view and dashboard widget that:
- Implements the WOH logic from the Sea_Air Release tab
- For each part with a pending sea shipment, calculates:
  - WOH before sea arrives (target: 0 — if negative, air freight may be needed)
  - WOH when sea arrives (target: 4 weeks)
  - Estimated cost of air vs. sea
- Outputs a recommendation per part: `no_action | release_to_sea | expedite_partial_air | management_review`

---

## 8. Technical Architecture

```
Data Sources
  MieTrak (CSV export, manual trigger)
  Customer Forecast (CSV, weekly drop)
  Manual inputs (demand factor, EOM counts)
        |
        v
Ingestion Layer
  SharePoint folder / shared mailbox
  Fabric Data Factory pipeline
  Schema validation notebook
        |
        v
OneLake — Bronze Layer
  Raw files, timestamped, source-tagged
        |
        v
OneLake — Silver Layer
  Cleaned, standardized, deduplicated
  Part key normalization
  Date normalization
  Customer part number mapping applied
        |
        v
OneLake — Gold Layer
  dim_* and fact_* tables (see Section 6)
  vw_projected_supply_demand
  vw_part_criticality
  vw_shipping_recommendation
        |
        v
Presentation & Action Layer
  Power BI semantic model (Direct Lake)
  Power BI dashboard — Planner view
  Fabric Activator / Power Automate — alerts
  Azure OpenAI / Copilot — digest agent (stretch)
```

**Development tooling:**
- Fabric workspace linked to GitHub repo via Git integration
- Antigravity used as AI coding accelerator for notebook and pipeline development
- Python (PySpark / pandas) for transformation notebooks
- SQL for Gold layer views and business logic

---

## 9. Open Questions (Blocking)

| # | Question | Who to Ask | Blocks |
|---|---|---|---|
| OQ-01 | How is US on-hand inventory accurately extracted if not through Flexiss? | Rich / Christy | F-01 pipeline design |
| OQ-02 | What columns does the MieTrak inventory report include? What does the open orders report look like? | Christy (screen share) | Silver layer schema |
| OQ-03 | How is the DEMAND FACTOR set per part? When is it adjusted away from 1.00? | Rich | F-02 algorithm accuracy |
| OQ-04 | Does "DO NOT REORDER" exist as a field in MieTrak, or is it only in spreadsheet notes? | Rich | dim_part.active_status |
| OQ-05 | How is the lead time to next sea release determined — fixed schedule, or variable? | Rich | F-02 ordering algorithm |
| OQ-06 | Who are the roles in the release workflow — Rich enters, Cindy approves, who else? | Tim / Christy | F-07 scope and workflow design |
| OQ-07 | Does the Giant forecast come in a consistent CSV format? What columns does it have? | Christy / Rich | F-01 forecast ingestion |
| OQ-08 | Are MieTrak US and Taiwan divisions exported as separate reports or one combined report? | Christy | Ingestion split logic |

---

## 10. Out-of-Scope Risks & Assumptions

- **Assumption:** MieTrak can export reports as CSV or Excel. Columns in those exports will be consistent enough to define a stable schema.
- **Assumption:** MRP has or can obtain a Microsoft Fabric trial or paid capacity for production use. (Developer trial confirmed for ~50 days.)
- **Assumption:** The ordering algorithm from the instructions screenshot applies universally to all parts except Carbon Forks, which have a manually estimated usage/month.
- **Risk:** US OEM inventory requires a paper EOM count. This cannot be automated in MVP and will remain a manual data entry step.
- **Risk:** Implicit business logic (manual overrides, special customer handling, "WATCH REORDER" flags) may not be fully captured before build begins. Rich interview is critical before Week 3.

---

## 11. Sprint Plan

| Sprint | Weeks | Deliverables |
|---|---|---|
| Sprint 0 | Week 1 | Rich interview → answers to OQ-01 through OQ-08. Obtain sample MieTrak CSVs. Finalize data contract (column mapping). Set up Fabric workspace + GitHub repo + Antigravity. |
| Sprint 1 | Week 2 | Bronze layer ingestion pipeline. Schema validation. First Silver layer tables: dim_part, fact_inventory_snapshot, fact_sales_order_line. |
| Sprint 2 | Week 3 | Gold layer: remaining fact tables. Implement ordering algorithm in SQL/notebook. Validate against spreadsheet output for 10 test parts. |
| Sprint 3 | Week 4 | Power BI dashboard (F-04). PO Needs report (F-03). At least one alert type (F-05). |
| Sprint 4 | Weeks 5–6 | AI digest agent or sea/air recommendation (stretch). Demo polish. Handoff documentation for Rich. Demo to professor + Tim and Christy. |

---

## 12. Success Criteria

The MVP is considered successful when:
1. Rich can trigger a CSV export from MieTrak, drop it in the designated folder, and see the Power BI dashboard refresh with updated part risk without touching the spreadsheet
2. The PO Needs output matches what the current spreadsheet produces for the same input data
3. Tim can identify the top 3 at-risk parts within 60 seconds of opening the dashboard
4. At least one AI-generated alert fires correctly in the demo environment

---

*Questions or updates? Open a GitHub issue tagged `prd-feedback` or message Preston.*
