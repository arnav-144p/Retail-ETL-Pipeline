from pathlib import Path
import re
from typing import List

# matches: sales_2025-12-24_store_1.csv
FILENAME_RE = re.compile(r"^sales_(\d{4}-\d{2}-\d{2})_store_(\d+)\.csv$")

def discover_available_dates(sample_data_dir: Path) -> List[str]:
    """
    Reads filenames from api/sample_data and returns sorted unique dates (YYYY-MM-DD).
    """
    dates = set()
    if not sample_data_dir.exists():
        return []

    for p in sample_data_dir.iterdir():
        if not p.is_file():
            continue
        m = FILENAME_RE.match(p.name)
        if m:
            dates.add(m.group(1))

    return sorted(dates)