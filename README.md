# Retail ETL Pipeline

This project simulates a real-world retail business scenario where multiple stores generate daily sales data. Instead of manually consolidating CSV files, this solution implements an automated ETL pipeline that extracts sales data from a REST API, transforms and cleans the data, and loads it into a centralized PostgreSQL database. To stress-test database indexing and validate the pipeline under massive data loads without exposing real Personally Identifiable Information (PII), this project utilizes a synthetic data generator. It uses the Python `Faker` library to safely bypass privacy constraints and generate 500,000 realistic retail records (5 stores × 2 simulated days × 50,000 transactions/day).

The pipeline is designed to run automatically on a schedule, ensuring up-to-date data in the database without manual intervention.

## Business Problem

A small retail company receives daily sales data from multiple stores. Previously, an analyst manually consolidated these files to produce reports a process prone to:

- Human errors
- Data inconsistencies
- Delays in reporting
- Lack of automation


The company needed a reliable, automated ETL pipeline to:
- Collect store sales data daily
- Clean and validate the data
- Store it in a centralized database
- Safely test system loads using PII-compliant, massive synthetic datasets

## Architecture
<!-- <div align="center">
  <img width="400" height="450" alt="image (6)" src="https://github.com/user-attachments/assets/35f0472b-7ddd-4a6e-b101-ae9e769f1cb4" />
</div> -->

``` mermaid
flowchart TD
    %% Styling configurations
    classDef highlight fill:#f4ebf9,stroke:#9c27b0,stroke-width:2px,color:#000,stroke-dasharray: 5 5
    classDef box fill:#ffffff,stroke:#333333,stroke-width:2px,color:#000
    classDef cylinder fill:#ffffff,stroke:#333333,stroke-width:2px,color:#000

    %% Nodes
    A["Creates 500K Synthetic Rows"]:::highlight
    B["Flask API<br>Serves Mock Data Source"]:::box
    C["Extract<br>Fetch API Data (JSON/CSV)"]:::box
    D["Transform<br>Clean, Deduplicate & Validate"]:::box
    E["Load<br>psycopg2 Upserts"]:::box
    F[("PostgreSQL<br>Central Database")]:::cylinder

    %% Connections
    A -->|Bypasses PII| B
    B --> C
    C --> D
    D --> E
    E --> F
  ```

## Tech Stack

| Component       | Technology            |
| --------------- | --------------------- |
| Programming     | Python                |
| API Simulation  | Flask                 |
| Data Processing | Pandas                |
| Database        | PostgreSQL            |
| Synthetic Data  | Faker                 |
| Configuration   | YAML                  |
| Scheduling      | Cron / Shell Script   |
| Logging         | Python logging module |

## Project Structure
<!-- <img width="660" height="718" alt="image" src="https://github.com/user-attachments/assets/7cc332e5-73a0-4687-91d0-f1f4ebe3f8ed" /> -->
<!-- <img width="660" height="718" alt="image" src="https://github.com/user-attachments/assets/781e9f7f-adc2-4f14-8ce2-5edfee99cc6c" /> -->
<!-- <img width="660" height="718" alt="image" src="https://github.com/user-attachments/assets/c805f757-610b-4cc2-b5bc-3ce61a8ce8c1" /> -->
```text
retail-etl-pipeline/
│
├── api/
│   ├── app.py                      # Flask mock API serving daily sales
│   └── sample data/                # Directory for synthetic CSVs
│
├── etl_pipeline/
│   ├── main.py                     # Main orchestration script
│   ├── extract.py                  # API extraction logic
│   ├── transform.py                # Pandas data cleaning & validation
│   ├── load.py                     # PostgreSQL connection & upsert logic
│   └── discover.py                 # File discovery utility
│
├── config/
│   └── config.yaml                 # Pipeline & Database configurations
│
├── logs/
│   └── pipeline.log                # Centralized ETL execution logs
│
├── schema.sql                      # SQL DDL for database setup
├── generate_synthetic_data.py      # Synthetic data generation script
└── run_pipeline.sh                 # Bash execution script for Cron
```

## ETL Pipeline Workflow

### Generate (Testing & Compliance)
- Uses a Python script (`generate_synthetic_data.py`) utilizing `Faker`.
- Synthesizes high-fidelity, timezone-accurate (`+05:45`) daily transactions.
- Allows for stress testing (e.g., 50k+ rows per store) while completely bypassing PII/privacy constraints.

### Extract
- Fetches sales data from the Flask REST API
- Supports both JSON and CSV response formats
- Includes a chaos mode to test how the pipeline handles unreliable data sources, mimicking real-world production conditions

### Transform
Cleans and validates every record before it reaches the database:
- **Missing values** — fills gaps with sensible defaults
- **Data type corrections** — ensures consistency across all fields
- **Business rule checks** — rejects negative prices, zero quantities, and missing IDs
- **Duplicate removal** — keeps only the most recent version of each transaction

Supports strict mode (stops on bad data) and lenient mode (skips bad rows and continues), making it flexible across environments

### Load
- Loads cleaned data into a PostgreSQL database efficiently and safely
- Automatically registers new stores and products before inserting sales records
- Designed to be safely rerun without creating duplicate records
- Timestamps every record so the team always knows when data was last refreshed


## Production-Oriented Design
This pipeline is designed with production-oriented execution principles in mind:

### Privacy & Scale Testing
- **PII Compliance:** Algorithmically generated data ensures zero risk of leaking real customer information during development.
- **Load Testing:** Easily scalable configuration allows testing database write performance and pipeline memory management under heavy strain.

### Runs Once Per Day
- The job executes once per day to avoid overlapping runs and reduce database contention
- A fixed execution window (02:00 UTC) ensures predictable batch processing and stable performance

### Fixed Execution Window
- Scheduled during off-peak hours to minimize load impact
- Provides deterministic daily snapshots of transactional data

### Idempotent by Design
- The pipeline is safe to rerun
- Duplicate transactions are prevented through:
  - Deduplication logic in the transform layer
  - Safe loading strategies in the database layer
- Re-running the same batch produces the same end state

### Checkpoint / Source Date Tracking
- Each batch includes a source_date column
- This allows:
  - Partition-level reprocessing
  - Easier auditing
  - Deterministic replay of specific days

### Backfill Support
- Historical data can be reprocessed safely
- Because the pipeline is idempotent, past dates can be replayed without creating duplicates
- This enables deterministic backfills from a known checkpoint

## Database Design

The schema is a small star-schema design with referential integrity and defensive constraints, not a single flat table:

**stores** (dimension)
- `store_id` (PK)
- `store_name`

**products** (dimension)
- `product_id` (PK)
- `product_name`

**sales_transactions** (fact)
- `transaction_id` (PK)
- `store_id` (FK → stores)
- `product_id` (FK → products)
- `quantity` (`CHECK`: <> 0)
- `unit_price` (`CHECK`: >= 0)
- `currency` (default: `NPR`)
- `transaction_ts`
- `source_date`
- `ingested_at` (default: `NOW()`)

Indexes on `source_date` and `(store_id, source_date)` speed up the most common analytical queries (daily and per-store reporting).

The schema is defined in: `database/schema.sql`

## How to Run the Project

### 1. Clone Repository
```bash
git clone https://github.com/arnav-144p/Retail-ETL-Pipeline.git
cd retail-etl-pipeline
```
### 2. Create Virtual Environment
```bash
python -m venv venv
source venv/bin/activate   # Mac/Linux
venv\Scripts\activate      # Windows
```
### 3. Install Dependencies
```bash
pip install -r requirements.txt
```
### 4. Setup PostgreSQL
Create a PostgreSQL database

Run:
```bash
psql -U <username> -d <database> -f database/schema.sql
```
Update database credentials in: ```config/config.yaml```

### 5. Generate Synthetic Data
Bypass manual file creation and populate the target directory with massive, high-fidelity mock data for the pipeline to process.
```bash
python generate_synthetic_data.py
```

### 6. Start the API
Serve the generated synthetic files via the Flask REST API.
```bash
python api/app.py
```
### 6. Run ETL Pipeline
```bash
python -m etl_pipeline.main
```
Or via shell script:

```
./run_pipeline.sh
```

## Automation
This pipeline can be scheduled using cron to run automatically.

### 1. Make the Script Executable
```bash
chmod +x run_pipeline.sh
```

### 2. Edit Crontab
Open cron editor:
```bash
crontab -e
```
Add this line:
```bash
CRON_TZ=UTC
0 2 * * * /full/path/to/RETAIL_ETL_PROJECT/run_pipeline.sh  
```
Save and exit.

### 3. Verify Cron Entry
```bash
crontab -l
```
You should see:
```bash
CRON_TZ=UTC
0 2 * * * /full/path/to/RETAIL_ETL_PROJECT/run_pipeline.sh  
```

Now, the ETL pipeline runs daily at 02:00 UTC using cron scheduling.
The wrapper script(```run_pipeline.sh```) activates the virtual environment and logs execution
details to ```logs/pipeline.log```.

#### Cron only works on Linux/macOS. For Windows, use Task Scheduler.
