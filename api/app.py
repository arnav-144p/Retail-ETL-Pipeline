from flask import Flask, request, jsonify, Response
import csv
import os
from datetime import datetime
from io import StringIO

app = Flask(__name__)

DATA_DIR = os.path.join(os.path.dirname(__file__), "sample data")

REQUIRED_FIELDS = [
    "transaction_id", "store_id", "product_id",
    "quantity", "unit_price", "currency", "transaction_ts"
]

def load_csv_for_date_store(date_str: str, store_id: int):
    fname = f"sales_{date_str}_store_{store_id}.csv"
    path = os.path.join(DATA_DIR, fname)
    if not os.path.exists(path):
        return []

    rows = []
    with open(path, "r", newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for r in reader:
            rows.append(r)
    return rows

@app.get("/health")
def health():
    return jsonify({"status": "ok"})

@app.get("/sales/daily")
def sales_daily():
    """
    GET /sales/daily?date=YYYY-MM-DD&store_id=1&format=json|csv
    """
    date_str = request.args.get("date")
    store_id = request.args.get("store_id", type=int)
    out_format = request.args.get("format", "json").lower()

    if not date_str:
        return jsonify({"error": "Missing required query param: date=YYYY-MM-DD"}), 400
    try:
        datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        return jsonify({"error": "Invalid date format. Use YYYY-MM-DD"}), 400

    if not store_id:
        return jsonify({"error": "Missing required query param: store_id"}), 400

    data = load_csv_for_date_store(date_str, store_id)

    # Simulate realism toggles (optional)
    chaos = request.args.get("chaos", "0")
    if chaos == "1" and data:
        # duplicate the first row to simulate duplicates
        data = data + [data[0]]

    payload = {
        "meta": {
            "date": date_str,
            "store_id": store_id,
            "row_count": len(data),
        },
        "data": data
    }

    if out_format == "csv":
        # convert to CSV response
        output = StringIO()
        writer = csv.DictWriter(output, fieldnames=REQUIRED_FIELDS)
        writer.writeheader()
        for row in data:
            writer.writerow({k: row.get(k, "") for k in REQUIRED_FIELDS})
        return Response(output.getvalue(), mimetype="text/csv")

    return jsonify(payload)

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5001, debug=True)