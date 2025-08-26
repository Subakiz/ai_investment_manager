#!/bin/bash

# AlphaGen Data Pipeline Runner
# This script runs the daily data collection pipeline

set -e

# Configuration
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
LOG_FILE="$PROJECT_DIR/logs/pipeline_runner.log"

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m'

log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S') - $1" | tee -a "$LOG_FILE"
}

log_error() {
    echo -e "${RED}$(date '+%Y-%m-%d %H:%M:%S') - ERROR: $1${NC}" | tee -a "$LOG_FILE"
}

log_success() {
    echo -e "${GREEN}$(date '+%Y-%m-%d %H:%M:%S') - SUCCESS: $1${NC}" | tee -a "$LOG_FILE"
}

# Change to project directory
cd "$PROJECT_DIR"

# Activate virtual environment if it exists
if [ -f "venv/bin/activate" ]; then
    source venv/bin/activate
    log_message "Virtual environment activated"
fi

# Check if .env file exists
if [ ! -f ".env" ]; then
    log_error ".env file not found. Please run setup.sh first."
    exit 1
fi

# Parse command line arguments
COLLECTION_TYPE="all"
DAYS_BACK=1

while [[ $# -gt 0 ]]; do
    case $1 in
        --type)
            COLLECTION_TYPE="$2"
            shift 2
            ;;
        --days)
            DAYS_BACK="$2"
            shift 2
            ;;
        --help)
            echo "Usage: $0 [--type all|market|news|financials] [--days N]"
            echo "  --type: Type of data to collect (default: all)"
            echo "  --days: Number of days back to collect (default: 1)"
            exit 0
            ;;
        *)
            log_error "Unknown option: $1"
            exit 1
            ;;
    esac
done

log_message "Starting AlphaGen data pipeline collection"
log_message "Collection type: $COLLECTION_TYPE"
log_message "Days back: $DAYS_BACK"

# Run the data collection
if python -m src.data_pipeline.pipeline collect --type "$COLLECTION_TYPE" --days "$DAYS_BACK"; then
    log_success "Data pipeline collection completed successfully"
    exit 0
else
    log_error "Data pipeline collection failed"
    exit 1
fi