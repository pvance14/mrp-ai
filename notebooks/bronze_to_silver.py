# Bronze to Silver Data Transformation Notebook
# This script reads raw CSV files from the Lakehouse Bronze layer, cleans the data,
# and writes Delta tables to the Silver layer.

from pyspark.sql import SparkSession
from pyspark.sql.functions import col, lit, current_date, to_date

# Initialize Spark session (Fabric normally does this automatically)
spark = SparkSession.builder.appName("BronzeToSilver").getOrCreate()

# Base paths for the lakehouse in Fabric
bronze_path = "Files/Bronze"
silver_path = "Tables"

# ==========================================
# 1. Ingest Bronze Data
# ==========================================
# Read Inventory
df_inventory_raw = spark.read.format("csv").option("header", "true").load(f"{bronze_path}/mietrak_inventory.csv")

# Read Orders
df_orders_raw = spark.read.format("csv").option("header", "true").load(f"{bronze_path}/mietrak_orders.csv")

# Read Forecast
df_forecast_raw = spark.read.format("csv").option("header", "true").load(f"{bronze_path}/customer_forecast.csv")

# ==========================================
# 2. Transform and Write Silver Tables
# ==========================================

# --- dim_part ---
# Deduplicate parts from inventory to create a basic part dimension
df_dim_part = df_inventory_raw.select(
    col("PartNumber").alias("part_id"),
    col("Description").alias("description")
).dropDuplicates(["part_id"])

# Add default columns per PRD schema
df_dim_part = df_dim_part.withColumn("active_status", lit("ACTIVE")) \
    .withColumn("demand_factor", lit(1.00))

df_dim_part.write.format("delta").mode("overwrite").saveAsTable("dim_part")


# --- fact_inventory_snapshot ---
df_fact_inventory = df_inventory_raw.select(
    current_date().alias("snapshot_date"),
    col("PartNumber").alias("part_id"),
    col("Location").alias("location_id"),
    col("OnHandQty").cast("int").alias("on_hand_qty"),
    lit("MieTrak").alias("source_system")
)

df_fact_inventory.write.format("delta").mode("overwrite").saveAsTable("fact_inventory_snapshot")


# --- fact_sales_order_line ---
df_sales_orders = df_orders_raw.filter(col("OrderType") == "SalesOrder").select(
    col("OrderNumber").alias("order_number"),
    col("PartNumber").alias("part_id"),
    col("Division").alias("division"),
    to_date(col("DueDate")).alias("promise_date"),
    col("OpenQty").cast("int").alias("open_qty"),
    lit("OPEN").alias("status")
)

df_sales_orders.write.format("delta").mode("overwrite").saveAsTable("fact_sales_order_line")


# --- fact_purchase_order_line ---
df_purchase_orders = df_orders_raw.filter(col("OrderType") == "PurchaseOrder").select(
    col("OrderNumber").alias("po_number"),
    col("PartNumber").alias("part_id"),
    to_date(col("DueDate")).alias("due_date"),
    col("OpenQty").cast("int").alias("open_qty"),
    lit("OPEN").alias("status")
)

df_purchase_orders.write.format("delta").mode("overwrite").saveAsTable("fact_purchase_order_line")


# --- fact_forecast ---
df_fact_forecast = df_forecast_raw.select(
    col("Customer").alias("customer_id"),
    col("PartNumber").alias("part_id"),
    to_date(col("ForecastDate")).alias("forecast_date"),
    col("Quantity").cast("int").alias("forecast_qty"),
    current_date().alias("upload_date")
)

df_fact_forecast.write.format("delta").mode("overwrite").saveAsTable("fact_forecast")

print("Bronze-to-Silver transformation complete. Silver tables written to Delta format.")
