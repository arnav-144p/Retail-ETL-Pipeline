import os
import csv
import random
from datetime import datetime, timedelta
try:
    from faker import Faker
except ImportError:
    print("Please install Faker: pip install faker")
    exit(1)

# Configuration for Synthetic Generation
DATA_DIR = os.path.join(os.path.dirname(__file__), "api", "sample data")
TARGET_DATES = ["2026-04-28", "2026-04-29"] # Dates to simulate
STORES = [1, 2, 3, 4, 5]                    # Expanded store count for scale
RECORDS_PER_STORE_DAY = 50000               # Scale this up for massive datasets

fake = Faker()

def generate_transaction_ts(target_date: str) -> str:
    """Generates a random timestamp within the target date with +05:45 offset."""
    base_date = datetime.strptime(target_date, "%Y-%m-%d")
    random_seconds = random.randint(0, 86399) # Seconds in a day
    tx_time = base_date + timedelta(seconds=random_seconds)
    # Output matching the required format: 2025-12-24T10:05:00+05:45
    return tx_time.strftime("%Y-%m-%dT%H:%M:%S+05:45")

def generate_synthetic_csv(date_str: str, store_id: int, num_records: int):
    os.makedirs(DATA_DIR, exist_ok=True)
    filename = f"sales_{date_str}_store_{store_id}.csv"
    filepath = os.path.join(DATA_DIR, filename)

    print(f"Generating {num_records} synthetic records for Store {store_id} on {date_str}...")

    with open(filepath, mode="w", newline="", encoding="utf-8") as f:
        writer = csv.writer(f)
        # Header matching schema.sql and app.py
        writer.writerow(["transaction_id", "store_id", "product_id", "quantity", "unit_price", "currency", "transaction_ts"])

        for i in range(1, num_records + 1):
            # Pad the sequential ID for realism
            tx_id = f"tx_{date_str}_{store_id}_{str(i).zfill(6)}"
            
            # Simulate realistic retail behavior (e.g., Pareto principle on products)
            product_id = random.choices(
                population=range(100, 150), # 50 distinct products
                weights=[random.randint(1, 100) for _ in range(50)], # Weighted popularity
                k=1
            )[0]
            
            # Bulk vs Single item purchasing
            quantity = random.choices([1, 2, 3, 4, 5, 10, 20], weights=[50, 25, 10, 5, 5, 3, 2], k=1)[0]
            
            # Unit prices ending in .99 or .50 for retail realism
            base_price = random.randint(50, 5000)
            unit_price = base_price + random.choice([0.00, 0.50, 0.99])
            
            currency = "NPR"
            tx_ts = generate_transaction_ts(date_str)

            writer.writerow([tx_id, store_id, product_id, quantity, f"{unit_price:.2f}", currency, tx_ts])

    print(f"Saved: {filepath} ({os.path.getsize(filepath) / (1024 * 1024):.2f} MB)")

if __name__ == "__main__":
    for d in TARGET_DATES:
        for s in STORES:
            generate_synthetic_csv(d, s, RECORDS_PER_STORE_DAY)
    print("Massive synthetic data generation complete. Ready for ETL extraction.")
