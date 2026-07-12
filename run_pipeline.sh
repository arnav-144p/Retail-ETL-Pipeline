#!/bin/bash

# ==============================
# Retail ETL Daily Cron Runner
# Runs at 02:00 UTC
# ==============================

# Exit immediately if a command fails
set -e

# project path
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

# Log file
LOG_FILE="$PROJECT_DIR/logs/pipeline.log"

# Timestamp
echo "----------------------------------------" >> "$LOG_FILE"
echo "ETL Run Started: $(date -u)" >> "$LOG_FILE"

# Navigate to project
cd "$PROJECT_DIR" || exit 1

# Activate virtual environment
source venv/bin/activate

# Run ETL pipeline
python -m etl_pipeline.main >> "$LOG_FILE" 2>&1

# Deactivate virtual environment
deactivate

echo "ETL Run Completed: $(date -u)" >> "$LOG_FILE"
echo "----------------------------------------" >> "$LOG_FILE"
