#!/bin/bash

# Cron job setup for AlphaGen data pipeline
# This script sets up cron jobs for automated data collection

set -e

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
CRON_FILE="/tmp/alphagen_cron"

echo "Setting up cron jobs for AlphaGen data pipeline..."

# Create cron job entries
cat > "$CRON_FILE" << EOF
# AlphaGen Personal Investment Platform - Automated Data Collection
# Generated on $(date)

# Daily market data collection after IDX close (4:30 PM WIB = 9:30 UTC)
30 9 * * 1-5 cd $PROJECT_DIR && ./scripts/run_pipeline.sh --type market --days 1 >> logs/cron.log 2>&1

# Daily news data collection after market close (4:45 PM WIB = 9:45 UTC)
45 9 * * 1-5 cd $PROJECT_DIR && ./scripts/run_pipeline.sh --type news --days 1 >> logs/cron.log 2>&1

# Weekly financial statements collection (Sundays at 10:00 UTC)
0 10 * * 0 cd $PROJECT_DIR && ./scripts/run_pipeline.sh --type financials --days 7 >> logs/cron.log 2>&1

# Health check every 6 hours
0 */6 * * * cd $PROJECT_DIR && python -m src.data_pipeline.pipeline health >> logs/health_check.log 2>&1

# Log rotation weekly (Sundays at 11:00 UTC)
0 11 * * 0 find $PROJECT_DIR/logs -name "*.log" -size +50M -exec gzip {} \; >> logs/maintenance.log 2>&1

EOF

# Install cron jobs
if crontab "$CRON_FILE"; then
    echo "✅ Cron jobs installed successfully!"
    echo ""
    echo "Scheduled jobs:"
    echo "- Market data: Daily at 9:30 UTC (4:30 PM WIB) on weekdays"
    echo "- News data: Daily at 9:45 UTC (4:45 PM WIB) on weekdays"
    echo "- Financial statements: Weekly on Sundays at 10:00 UTC"
    echo "- Health checks: Every 6 hours"
    echo "- Log rotation: Weekly on Sundays at 11:00 UTC"
    echo ""
    echo "To view current cron jobs: crontab -l"
    echo "To remove cron jobs: crontab -r"
else
    echo "❌ Failed to install cron jobs"
    exit 1
fi

# Cleanup
rm "$CRON_FILE"

echo ""
echo "Note: Make sure the project directory path is correct and the scripts have execute permissions."
echo "You can test the pipeline manually with: ./scripts/run_pipeline.sh --type all --days 1"