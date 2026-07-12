from pathlib import Path
from datetime import datetime

import pandas as pd

from logs.logger import build_logger
from etl_pipeline.extract import fetch_store_sales
from etl_pipeline.transform import clean_and_validate
from etl_pipeline.load import connect, ensure_dimensions, upsert_sales
from etl_pipeline.discover import discover_available_dates


BASE_DIR = Path(__file__).resolve().parents[1]           # project root
CONFIG_PATH = BASE_DIR / "config" / "config.yaml"
SAMPLE_DATA_DIR = BASE_DIR / "api" / "sample data"


def load_config(path: Path):
    import yaml
    with open(path, "r", encoding="utf-8") as f:
        return yaml.safe_load(f)


def today_local_date_str() -> str:
    return datetime.now().strftime("%Y-%m-%d")


def run_one_date(cfg: dict, source_date: str, log):
    base_url = cfg["api"]["base_url"]
    stores = cfg["api"]["stores"]
    out_format = cfg["api"].get("format", "json")
    chaos = bool(cfg["api"].get("chaos", False))

    strict = bool(cfg["etl"].get("strict_validation", False))
    default_currency = cfg["etl"].get("default_currency", "NPR")

    log.info(f"Starting ETL for source_date={source_date}, stores={stores}, format={out_format}")

    # Extract + Transform per store
    all_frames = []
    for store_id in stores:
        try:
            log.info(f"Extracting store_id={store_id}")
            df_raw = fetch_store_sales(base_url, source_date, store_id, out_format, chaos=chaos)
            log.info(f"Extracted rows={len(df_raw)} store_id={store_id}")

            df_clean = clean_and_validate(
                df_raw,
                source_date,
                default_currency=default_currency,
                strict=strict
            )
            log.info(f"Clean rows={len(df_clean)} store_id={store_id}")

            all_frames.append(df_clean)
        except Exception as e:
            log.error(f"Store {store_id} failed: {e}")

    if not all_frames:
        log.warning(f"No store dataframes produced for {source_date}. Skipping.")
        return

    all_frames = [df for df in all_frames if df is not None and not df.empty]
    if not all_frames:
        log.warning(f"No data for {source_date}. Skipping.")
        return
    df_all = pd.concat(all_frames, ignore_index=True)
    
    # Combine
    df_all = pd.concat(all_frames, ignore_index=True)
    log.info(f"Total rows after combine={len(df_all)} for {source_date}")

    # ✅ IMPORTANT: If nothing to load, don’t even connect to DB
    if df_all.empty:
        log.warning(f"Total rows=0 for {source_date}. Skipping DB load.")
        return

    # Load
    conn = connect(cfg["database"])
    try:
        conn.autocommit = False
        ensure_dimensions(conn, df_all)
        upsert_sales(conn, df_all)
        conn.commit()
        log.info(f"Load successful (commit) for {source_date}.")
    except Exception as e:
        conn.rollback()
        log.error(f"Load failed (rollback) for {source_date}: {e}")
        raise
    finally:
        conn.close()


def run():
    log = build_logger("daily-retail-etl")

    # Load config from a stable absolute path
    cfg = load_config(CONFIG_PATH)

    source_date_cfg = cfg.get("etl", {}).get("source_date")

    # Case 1: source_date = "ALL" -> backfill all discovered dates
    if source_date_cfg is not None and str(source_date_cfg).upper() == "ALL":
        dates = discover_available_dates(SAMPLE_DATA_DIR)

        if not dates:
            log.warning(f'No dates discovered in "{SAMPLE_DATA_DIR}". Nothing to do.')
            return

        log.info(f"Discovered dates to process: {dates}")
        for d in dates:
            run_one_date(cfg, d, log)

        log.info("ALL-dates run complete.")
        return

    # Case 2: source_date specified as "YYYY-MM-DD"
    if source_date_cfg:
        source_date = str(source_date_cfg)
        run_one_date(cfg, source_date, log)
        return

    # Case 3: source_date is null -> run today
    source_date = today_local_date_str()
    run_one_date(cfg, source_date, log)


if __name__ == "__main__":
    run()