# Build Power BI Semantic Model Relationships
# This script uses Semantic Link (sempy) to programmatically establish the 
# relationships on the default MRPLakehouse semantic model.
# Run this inside a Microsoft Fabric Notebook attached to MRPLakehouse.

import sempy.fabric as fabric

dataset_name = "MRPLakehouse"

print(f"Configuring relationships for Semantic Model: {dataset_name}...")

# Define relationships: (Fact Table, Fact Column, Dim Table, Dim Column)
relationships = [
    ("vw_part_criticality", "part_id", "dim_part", "part_id"),
    ("vw_shipping_recommendation", "part_id", "dim_part", "part_id"),
    ("fact_inventory_snapshot", "part_id", "dim_part", "part_id"),
    ("fact_sales_order_line", "part_id", "dim_part", "part_id"),
    ("fact_purchase_order_line", "part_id", "dim_part", "part_id"),
    ("fact_forecast", "part_id", "dim_part", "part_id")
]

for from_table, from_col, to_table, to_col in relationships:
    try:
        fabric.create_relationship(
            dataset=dataset_name,
            from_table=from_table,
            from_column=from_col,
            to_table=to_table,
            to_column=to_col,
            cross_filtering_behavior="both",
            cardinality="many-to-one"
        )
        print(f"✅ Created many-to-one relationship: {from_table}[{from_col}] -> {to_table}[{to_col}]")
    except Exception as e:
        print(f"⚠️ Could not create relationship {from_table} -> {to_table}: {e}")

print("\nSemantic Model configuration finished! You can now build the Power BI Dashboard on this dataset.")
