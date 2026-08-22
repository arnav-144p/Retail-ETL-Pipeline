-- Dimension tables
CREATE TABLE IF NOT EXISTS stores (
  store_id INTEGER PRIMARY KEY,
  store_name TEXT
);

CREATE TABLE IF NOT EXISTS products (
  product_id INTEGER PRIMARY KEY,
  product_name TEXT
);

-- Fact table
CREATE TABLE IF NOT EXISTS sales_transactions (
  transaction_id TEXT PRIMARY KEY,
  store_id INTEGER NOT NULL REFERENCES stores(store_id),
  product_id INTEGER NOT NULL REFERENCES products(product_id),
  quantity INTEGER NOT NULL CHECK (quantity <> 0),
  unit_price NUMERIC(12,2) NOT NULL CHECK (unit_price >= 0),
  currency TEXT NOT NULL DEFAULT 'NPR',
  transaction_ts TIMESTAMPTZ NOT NULL,
  source_date DATE NOT NULL,
  ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW()
);

CREATE INDEX IF NOT EXISTS idx_sales_source_date ON sales_transactions(source_date);
CREATE INDEX IF NOT EXISTS idx_sales_store_date ON sales_transactions(store_id, source_date);
