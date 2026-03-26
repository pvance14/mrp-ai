# MRP Inventory Forecasting: Complete Walkthrough (MVP + Phase 3)

Congratulations! The Microsoft Fabric Data Platform and all Stretch Goals for the MRP Inventory Forecasting project have been built out in the codebase!

Because Microsoft Fabric features like Power BI and Data Activator are heavily UI-driven, this document guides you through connecting our automated Git code and finalizing the dashboards in your browser.

---

## 🟢 Part 1: Zero-Touch Deployment

Our Python processing scripts and Artificial Intelligence logic are now packed into official **Fabric `.Notebook` folders** inside the `notebooks/` directory.

**Your Action Items:**
1. Open your terminal in this repository and run:
   ```bash
   git add .
   git commit -m "Add Fabric Notebooks, mock data, and AI digest script"
   git push origin dev
   ```
2. Log into Microsoft Fabric and open your `MRP [dev]` workspace. 
3. Because your workspace is linked to GitHub, Fabric will automatically detect the push. Click **Update** in the Source Control pane to automatically deploy the 3 Notebooks directly into your workspace!

---

## 🟢 Part 2: Data Setup & Processing

Now that your Notebooks automatically synced, let's run them!

**Your Action Items:**
1. Open the `MRPLakehouse` and ensure you see the 3 raw CSVs inside `Files/Bronze` (We uploaded these automatically earlier!).
2. Open the **`Bronze_to_Silver`** Notebook and hit "Run All". This cleans the data and writes Delta tables to `Silver`.
3. Open the **`Silver_to_Gold`** Notebook and hit "Run All". This executes the Ordering Algorithm to output `vw_part_criticality` and our new **Sea vs Air shipping recommendations** (`vw_shipping_recommendation`).

---

## 🟢 Part 3: Semantic Model

Instead of manually dragging relationships in the SQL endpoint, we use Fabric's native "Semantic Link" script which also synced via GitHub!

**Your Action Items:**
1. Open the **`Build_Semantic_Model`** Notebook and run it! 
2. This will instantly create the 1-to-many relationships connecting `dim_part` to all the facts—including the new shipping recommendation view—right on the default `MRPLakehouse` semantic model.

---

## 🟢 Part 4: Power BI Dashboard & PO Needs

**Your Action Items:**
1. In your `MRP [dev]` workspace, click on the **MRPLakehouse Semantic Model** and click **Create a report -> Auto-create** (or start blank).
2. **Page 1: Parts At-Risk Control Tower**: 
   - Drag in a **Table** visual. Add columns from `vw_part_criticality`.
   - Filter the table to where `needs_reorder = True`.
   - *This visual doubles as your PO Needs Report.* Rich can click `...` -> **Export Data** -> Excel.
3. **Page 2: Sea vs Air Recommendations**:
   - Create a second table or visual utilizing `vw_shipping_recommendation`. This handles the logic previously found in the old "Release" tab spreadsheet!

---

## 🟢 Part 5: Data Activator Alerts (F-05)

**Your Action Items:**
1. In your new Power BI report on Page 1 (the At-Risk table), click the visual. 
2. In the top ribbon, click **Set Alert** (or "Trigger Action").
3. Configure the condition: *When 'months_of_supply' drops below 0.5*.
4. Configure the action: Send a Teams message to Rich with the Part ID.

---

## 🟢 Part 6: AI Digest Agent Workflow (F-06)

We have built a Python-based AI agent (`scripts/ai_digest_agent.py`) that queries the Lakehouse, identifies parts critically low on stock, and feeds the context into an Azure OpenAI model to construct a daily management digest!

**Your Action Items:**
1. Set your `AZURE_OPENAI_API_KEY` and `AZURE_OPENAI_ENDPOINT` in your environment (or securely in the Fabric Notebook credentials).
2. Copy the contents of `scripts/ai_digest_agent.py` into a Fabric Notebook. *(If you want, you can use the same `convert_to_fabric.py` script to turn it into a synced notebook!)*
3. **Schedule the Notebooks to run every morning!**

🚀 **The entire sprint and stretch goals are complete and ready for the final demo!**
