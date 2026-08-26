#!/bin/bash
# Daily job scraping script for UAE Job Intelligence Platform

set -e

# Configuration
PROJECT_DIR="/opt/uae-jobs"
LOG_FILE="/var/log/uae-jobs.log"
PYTHON_BIN="python3"

# Ensure log directory exists
mkdir -p $(dirname $LOG_FILE)

# Function to log with timestamp
log() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a $LOG_FILE
}

# Function to run Python script
run_python() {
    cd $PROJECT_DIR
    $PYTHON_BIN -c "
import sys
sys.path.insert(0, '.')
from src.ingestion.sources.rapidapi_linkedin import ScraperRotator
from src.orchestration.scheduler import DailyScheduler

scheduler = DailyScheduler()
scheduler.scrape_jobs()
"
}

# Main execution
log "Starting daily job scraping..."

if run_python; then
    log "Daily scrape completed successfully"
else
    log "ERROR: Daily scrape failed with exit code $?"
    exit 1
fi
