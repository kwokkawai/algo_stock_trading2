#!/usr/bin/env bash
# Daily automation: M1 health check + M2 paper run + journal EOD + day report.
#
# Usage:
#   ./scripts/daily_run.sh
#   SKIP_M1=1 ./scripts/daily_run.sh    # skip lint/tests (faster)
#
# Requires: OpenD running, config/settings.yaml, .venv

source "$(dirname "$0")/lib/common.sh"

myalgo2_require_venv
myalgo2_require_settings
myalgo2_require_opend
myalgo2_begin_log "daily_run"

myalgo2_run_m1_check
myalgo2_run_m2_status
myalgo2_run_m2_strategies
myalgo2_run_journal_eod
myalgo2_run_report day

echo "=== daily_run completed OK ==="
