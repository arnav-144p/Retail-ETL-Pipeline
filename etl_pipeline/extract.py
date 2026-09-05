import requests
import pandas as pd
from io import StringIO

def fetch_store_sales(base_url: str, date_str: str, store_id: int, out_format: str, chaos: bool = False):
    params = {"date": date_str, "store_id": store_id, "format": out_format}
    if chaos:
        params["chaos"] = "1"

    url = f"{base_url.rstrip('/')}/sales/daily"
    resp = requests.get(url, params=params, timeout=20)
    resp.raise_for_status()

    if out_format == "csv":
        df = pd.read_csv(StringIO(resp.text))
        return df

    payload = resp.json()
    df = pd.DataFrame(payload.get("data", []))
    return df
