#!/usr/bin/env bash
# Weekly performance report (journal only — no strategy run).
#
# Usage:
#   ./scripts/weekly_report.sh

source "$(dirname "$0")/lib/common.sh"

myalgo2_require_venv
myalgo2_require_settings
myalgo2_begin_log "weekly_report"

# Optional: refresh fills from Futu if OpenD is up
if myalgo2_opend_available; then
  echo "--- Sync fills (OpenD available) ---"
  "$PYTHON" scripts/sync_fills.py
else
  echo "OpenD not running — skipping sync_fills (report uses local journal only)"
fi

myalgo2_run_report week

echo "=== weekly_report completed OK ==="
