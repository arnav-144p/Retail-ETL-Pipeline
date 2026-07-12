import pandas as pd

REQUIRED = ["transaction_id","store_id","product_id","quantity","unit_price","currency","transaction_ts"]

def clean_and_validate(df: pd.DataFrame, source_date: str, default_currency: str = "NPR", strict: bool = False):
    # Handle empty extracts
    if df is None or df.empty:
        return pd.DataFrame(columns=REQUIRED + ["source_date"])

    # Ensure required columns exist
    for col in REQUIRED:
        if col not in df.columns:
            df[col] = None

    # Normalize types
    df["store_id"] = pd.to_numeric(df["store_id"], errors="coerce").astype("Int64")
    df["product_id"] = pd.to_numeric(df["product_id"], errors="coerce").astype("Int64")
    df["quantity"] = pd.to_numeric(df["quantity"], errors="coerce").astype("Int64")
    df["unit_price"] = pd.to_numeric(df["unit_price"], errors="coerce")
    df["currency"] = df["currency"].fillna(default_currency).astype(str)
    df["transaction_id"] = df["transaction_id"].astype(str)

    # Parse timestamps (timezone-aware if possible)
    df["transaction_ts"] = pd.to_datetime(df["transaction_ts"], errors="coerce", utc=True)

    # Add ETL partition key
    df["source_date"] = pd.to_datetime(source_date).date()

    # Drop obvious bad rows (or fail if strict)
    problems = []

    # Null checks
    null_crit = df["transaction_id"].isna() | (df["transaction_id"].str.len() == 0)
    if null_crit.any():
        problems.append(f"Missing transaction_id rows={int(null_crit.sum())}")

    null_fk = df["store_id"].isna() | df["product_id"].isna()
    if null_fk.any():
        problems.append(f"Missing store_id/product_id rows={int(null_fk.sum())}")

    null_ts = df["transaction_ts"].isna()
    if null_ts.any():
        problems.append(f"Bad transaction_ts rows={int(null_ts.sum())}")

    # Business rules
    bad_qty = df["quantity"].isna() | (df["quantity"] == 0)
    if bad_qty.any():
        problems.append(f"Bad quantity rows={int(bad_qty.sum())}")

    bad_price = df["unit_price"].isna() | (df["unit_price"] < 0)
    if bad_price.any():
        problems.append(f"Bad unit_price rows={int(bad_price.sum())}")

    if problems and strict:
        raise ValueError("Validation failed: " + " | ".join(problems))

    # Non-strict: filter bad rows out
    good = ~(null_crit | null_fk | null_ts | bad_qty | bad_price)
    df = df.loc[good].copy()

    # Deduplicate by transaction_id (keep latest timestamp)
    df = df.sort_values("transaction_ts").drop_duplicates(subset=["transaction_id"], keep="last")

    # Keep only columns we load
    df = df[REQUIRED + ["source_date"]]
    return df