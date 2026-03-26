# Fabric notebook source

# METADATA ********************

# META {
# META   "kernel_info": {
# META     "name": "synapse_pyspark"
# META   },
# META   "dependencies": {
# META     "lakehouse": {
# META       "default_lakehouse": "94038775-e375-406d-ac6c-362b0ac84844",
# META       "default_lakehouse_name": "MRPLakehouse",
# META       "default_lakehouse_workspace_id": "19f5ade2-5ab6-4e67-9c26-157935db64e3"
# META     }
# META   }
# META }

# CELL ********************

# Silver to Gold Data Transformation Notebook
# This script reads from the clean Silver tables, applies the core Ordering Algorithm,
# and outputs the final time-phased Supply vs. Demand tables (Gold).

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, sum as _sum, lit, when

# Initialize Spark session
spark = SparkSession.builder.appName("SilverToGold").getOrCreate()

# Base paths
silver_path = "Tables"
gold_path = "Tables"

# ==========================================
# 1. Read Silver Data
# ==========================================
dim_part = spark.read.format("delta").load("dim_part")
fact_inventory = spark.read.format("delta").load("fact_inventory_snapshot")
fact_sales_orders = spark.read.format("delta").load("fact_sales_order_line")
fact_pos = spark.read.format("delta").load("fact_purchase_order_line")
fact_forecast = spark.read.format("delta").load("fact_forecast")

# ==========================================
# 2. Aggregations at the Part Level
# ==========================================

# Total On-Hand Stock (sum across locations)
agg_inventory = fact_inventory.groupBy("part_id").agg(_sum("on_hand_qty").alias("total_on_hand"))

# Total Incoming Stock (Open POs)
agg_pos = fact_pos.filter(col("status") == "OPEN") \
    .groupBy("part_id").agg(_sum("open_qty").alias("total_inbound"))

# Total Committed Stock (Open Sales Orders)
agg_sales = fact_sales_orders.filter(col("status") == "OPEN") \
    .groupBy("part_id").agg(_sum("open_qty").alias("total_committed"))

# Average Monthly Usage (Mock approximation from sum of 4 months forecast / 4)
agg_demand = fact_forecast.groupBy("part_id").agg((_sum("forecast_qty") / 4).alias("monthly_avg_usage"))

# ==========================================
# 3. Core Ordering Algorithm
# ==========================================
# Months of Supply = 
#  ( Stock On Hand 
#  + Stock Inbound (POs) 
#  + Pending Release Quantities (Setting 0 for MVP)
#  - (Monthly Avg Usage * Lead Time to Next Sea Release in months (Setting 1 for MVP)) )
#  / Monthly Avg Usage

# Join all aggregations to dim_part
vw_projected = dim_part.join(agg_inventory, "part_id", "left") \
    .join(agg_pos, "part_id", "left") \
    .join(agg_sales, "part_id", "left") \
    .join(agg_demand, "part_id", "left")

# Fill nulls with 0 for quantities
vw_projected = vw_projected.fillna({
    "total_on_hand": 0,
    "total_inbound": 0,
    "total_committed": 0,
    "monthly_avg_usage": 0
})

vw_projected = vw_projected.withColumn(
    "months_of_supply",
    when(col("monthly_avg_usage") > 0,
         (col("total_on_hand") + col("total_inbound") - (col("monthly_avg_usage") * 1.0)) / col("monthly_avg_usage")
    ).otherwise(lit(None))
)

# Exception handling / Flag Critical Parts
vw_projected = vw_projected.withColumn(
    "needs_reorder",
    when(col("months_of_supply") < 0, True).otherwise(False)
)

# Output vw_part_criticality to Gold
vw_projected.write.format("delta").mode("overwrite").saveAsTable("vw_part_criticality")

# ==========================================
# 4. Sea vs. Air Recommendation Engine (F-07)
# ==========================================
# Calculate Weeks On Hand (WOH) to determine if air freight is needed
# before a pending sea shipment arrives.

vw_shipping = vw_projected.filter(col("total_inbound") > 0).select(
    "part_id", "total_on_hand", "total_inbound", "monthly_avg_usage"
)

vw_shipping = vw_shipping.withColumn(
    "weekly_avg_usage", 
    when(col("monthly_avg_usage") > 0, col("monthly_avg_usage") / 4).otherwise(lit(0))
)

vw_shipping = vw_shipping.withColumn(
    "woh_before_sea",
    when(col("weekly_avg_usage") > 0, col("total_on_hand") / col("weekly_avg_usage")).otherwise(lit(999))
)

# Recommend expedite if WOH is critically low before arrival
vw_shipping = vw_shipping.withColumn(
    "shipping_recommendation",
    when(col("woh_before_sea") < 2, lit("EXPEDITE_AIR"))
    .when(col("woh_before_sea") < 4, lit("MANAGEMENT_REVIEW"))
    .otherwise(lit("RELEASE_TO_SEA"))
)

vw_shipping.write.format("delta").mode("overwrite").saveAsTable("vw_shipping_recommendation")

print("Silver-to-Gold transformation complete. Ordering algorithm results written to 'vw_part_criticality' and 'vw_shipping_recommendation' Delta tables.")


# METADATA ********************

# META {
# META   "language": "python",
# META   "language_group": "synapse_pyspark"
# META }
