import psycopg2
from psycopg2.extras import execute_values

UPSERT_SQL = """
INSERT INTO sales_transactions
(transaction_id, store_id, product_id, quantity, unit_price, currency, transaction_ts, source_date)
VALUES %s
ON CONFLICT (transaction_id) DO UPDATE SET
  store_id = EXCLUDED.store_id,
  product_id = EXCLUDED.product_id,
  quantity = EXCLUDED.quantity,
  unit_price = EXCLUDED.unit_price,
  currency = EXCLUDED.currency,
  transaction_ts = EXCLUDED.transaction_ts,
  source_date = EXCLUDED.source_date,
  ingested_at = NOW();
"""

def connect(db_cfg: dict):
    return psycopg2.connect(
        host=db_cfg["host"],
        port=db_cfg["port"],
        dbname=db_cfg["dbname"],
        user=db_cfg["user"],
        password=db_cfg["password"],
    )

def ensure_dimensions(conn, df):
    # Minimal “dimension loading”: insert stores/products referenced by facts
    stores = sorted({int(x) for x in df["store_id"].dropna().unique()})
    products = sorted({int(x) for x in df["product_id"].dropna().unique()})

    with conn.cursor() as cur:
        if stores:
            execute_values(cur,
                "INSERT INTO stores (store_id, store_name) VALUES %s ON CONFLICT (store_id) DO NOTHING",
                [(s, f"Store {s}") for s in stores]
            )
        if products:
            execute_values(cur,
                "INSERT INTO products (product_id, product_name) VALUES %s ON CONFLICT (product_id) DO NOTHING",
                [(p, f"Product {p}") for p in products]
            )

def upsert_sales(conn, df):
    rows = []
    for r in df.itertuples(index=False):
        rows.append((
            r.transaction_id,
            int(r.store_id),
            int(r.product_id),
            int(r.quantity),
            float(r.unit_price),
            str(r.currency),
            r.transaction_ts.to_pydatetime(),
            r.source_date
        ))

    with conn.cursor() as cur:
        execute_values(cur, UPSERT_SQL, rows, page_size=1000)