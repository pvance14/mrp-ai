# MRP Inventory Forecasting: Complete Walkthrough (MVP + Phase 3)

Congratulations! The Microsoft Fabric Data Platform and all Stretch Goals for the MRP Inventory Forecasting project have been built out in the codebase!

Because Microsoft Fabric features like Power BI and Data Activator are heavily UI-driven, this document guides you through running the scripts we prepared and finalizing the dashboards in your browser.

---

## 🟢 Part 1: Data Setup & Processing

We created `MRPLakehouse` directly in your `MRP [dev]` workspace, set up the `Bronze/Silver/Gold` folder architecture, and uploaded mock data.

**Your Action Items:**
1. Log into Microsoft Fabric and open `MRPLakehouse`.
2. Ensure you see the raw CSVs inside `Files/Bronze`.
3. Create a new Notebook, paste the contents of `notebooks/bronze_to_silver.py`, and run it. This cleans the data and writes Delta tables to `Silver`.
4. Create a second Notebook, paste `notebooks/silver_to_gold.py`, and run it. This executes the Ordering Algorithm to output `vw_part_criticality` and our new Phase 3 **Sea vs Air shipping recommendations** (`vw_shipping_recommendation`).

---

## 🟢 Part 2: Semantic Model (Direct Lake)

We use Fabric's native "Semantic Link" to build the Power BI relationships instantly.

**Your Action Items:**
1. Create a third Notebook attached to the Lakehouse.
2. Paste the contents of `notebooks/build_semantic_model.py` and run it. 
3. This creates the 1-to-many relationships connecting `dim_part` to all the facts—including the new shipping recommendation view!

---

## 🟢 Part 3: Power BI Dashboard & PO Needs

**Your Action Items:**
1. In your `MRP [dev]` workspace, click on the **MRPLakehouse Semantic Model** and click **Create a report -> Auto-create** (or start blank).
2. **Page 1: Parts At-Risk Control Tower**: 
   - Drag in a **Table** visual. Add columns from `vw_part_criticality`.
   - Filter the table to where `needs_reorder = True`.
   - *This visual doubles as your PO Needs Report.* Rich can click `...` -> **Export Data** -> Excel.
3. **Page 2: Sea vs Air Recommendations**:
   - Create a second table or visual utilizing `vw_shipping_recommendation`. This handles the logic previously found in the old "Release" tab spreadsheet!

---

## 🟢 Part 4: Data Activator Alerts (F-05)

**Your Action Items:**
1. In your new Power BI report on Page 1 (the At-Risk table), click the visual. 
2. In the top ribbon, click **Set Alert** (or "Trigger Action").
3. Configure the condition: *When 'months_of_supply' drops below 0.5*.
4. Configure the action: Send a Teams message to Rich with the Part ID.

---

## 🟢 Part 5: AI Digest Agent Workflow (F-06)

We have built a Python-based AI agent (`scripts/ai_digest_agent.py`) that queries the Lakehouse, identifies parts critically low on stock, and feeds the context into an Azure OpenAI model to construct a daily management digest!

**Your Action Items:**
1. Set your `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` in your environment (or securely in the Fabric Notebook credentials).
2. Copy the contents of `scripts/ai_digest_agent.py` into a Fabric Notebook.
3. Schedule the Notebook to run every morning at 8:00 AM! 

🚀 **The entire sprint and stretch goals are complete and ready for the final demo!**
