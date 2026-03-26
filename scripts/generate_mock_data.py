import csv
import random
from datetime import datetime, timedelta
import os

os.makedirs('mock_data', exist_ok=True)

# Common parts list reflecting "MR" parts from the PRD
parts = [
    {"part_id": "MR-03-084-K", "desc": "TR Skid Black"},
    {"part_id": "MR-03-119-CS", "desc": "ProductA Steel CS"},
    {"part_id": "MR-03-200-A", "desc": "Standard Axel"},
    {"part_id": "MR-04-101-C", "desc": "Carbon Fork Base"},
    {"part_id": "MR-05-999-X", "desc": "Test Part"}
]

# 1. MieTrak Inventory (Snapshot of what's currently on hand)
def generate_inventory():
    with open('mock_data/mietrak_inventory.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['PartNumber', 'Description', 'Location', 'OnHandQty'])
        for p in parts:
            # Taiwan Stock
            writer.writerow([p["part_id"], p["desc"], 'Taiwan_WH', random.randint(10, 500)])
            # US Stock
            writer.writerow([p["part_id"], p["desc"], 'US_WH', random.randint(5, 200)])

# 2. MieTrak Orders (Open Sales Orders & Purchase Orders)
def generate_orders():
    with open('mock_data/mietrak_orders.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['OrderNumber', 'OrderType', 'PartNumber', 'Division', 'DueDate', 'OpenQty'])
        
        base_date = datetime.now()
        for i in range(20):
            p = random.choice(parts)["part_id"]
            # Generate random due dates within the next 3 months
            due_date = base_date + timedelta(days=random.randint(5, 90))
            order_type = random.choice(["SalesOrder", "PurchaseOrder"])
            division = random.choice(["Taiwan", "US"])
            qty = random.randint(10, 300)
            writer.writerow([f"ORD-{1000+i}", order_type, p, division, due_date.strftime('%Y-%m-%d'), qty])

# 3. Customer Forecast (OEM demand like Giant)
def generate_forecast():
    with open('mock_data/customer_forecast.csv', 'w', newline='') as f:
        writer = csv.writer(f)
        writer.writerow(['Customer', 'PartNumber', 'ForecastDate', 'Quantity'])
        
        base_date = datetime.now()
        for p in parts:
            # Generate forecast for the next 4 months (beginning of each month)
            for m in range(1, 5):
                forecast_date = (base_date.replace(day=1) + timedelta(days=32 * m)).replace(day=1)
                writer.writerow(['Giant', p["part_id"], forecast_date.strftime('%Y-%m-%d'), random.randint(20, 150)])

if __name__ == "__main__":
    generate_inventory()
    generate_orders()
    generate_forecast()
    print("Mock data generated in 'mock_data/' directory.")
