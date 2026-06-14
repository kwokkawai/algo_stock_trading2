# Shared helpers for scheduled myAlgo2 shell jobs.
# Source from other scripts: source "$(dirname "$0")/lib/common.sh"

set -euo pipefail

MYALGO2_ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/../.." && pwd)"
cd "$MYALGO2_ROOT"

PYTHON="${MYALGO2_ROOT}/.venv/bin/python"
LOG_DIR="${MYALGO2_ROOT}/logs"
REPORT_DIR="${MYALGO2_ROOT}/logs/reports"
MARKET="${MYALGO2_MARKET:-HK}"

# Tier 1 strategies (keep in sync with src/strategy/registry.py)
TIER1_STRATEGIES=(
  sma_crossover
  ema_crossover
  donchian_breakout
  bollinger_rsi
  momentum_rotation
)

myalgo2_require_venv() {
  if [[ ! -x "$PYTHON" ]]; then
    echo "ERROR: Python venv not found at $PYTHON"
    echo "Run: cd \"$MYALGO2_ROOT\" && make install-dev"
    exit 1
  fi
}

myalgo2_require_settings() {
  if [[ ! -f "${MYALGO2_ROOT}/config/settings.yaml" ]]; then
    echo "ERROR: config/settings.yaml missing"
    echo "Run: cp config/settings.example.yaml config/settings.yaml"
    exit 1
  fi
}

myalgo2_opend_available() {
  local lsof_bin="/usr/sbin/lsof"
  if [[ ! -x "$lsof_bin" ]]; then
    lsof_bin="$(command -v lsof || true)"
  fi
  [[ -n "$lsof_bin" ]] && "$lsof_bin" -i :11111 2>/dev/null | grep -q Futu_Open
}

myalgo2_require_opend() {
  if ! myalgo2_opend_available; then
    echo "ERROR: Futu OpenD is not listening on 127.0.0.1:11111"
    echo "Start OpenD, log in to Futu HK, then retry."
    exit 1
  fi
}

myalgo2_begin_log() {
  local prefix="$1"
  mkdir -p "$LOG_DIR" "$REPORT_DIR"
  local stamp
  stamp="$(date +%Y%m%d_%H%M%S)"
  LOG_FILE="${LOG_DIR}/${prefix}_${stamp}.log"
  export LOG_FILE
  exec >>"$LOG_FILE" 2>&1
  echo "=== ${prefix} $(date '+%Y-%m-%d %H:%M:%S %Z') ==="
  echo "Project: $MYALGO2_ROOT"
  echo "Log file: $LOG_FILE"
}

myalgo2_run_m1_check() {
  if [[ "${SKIP_M1:-0}" == "1" ]]; then
    echo "SKIP_M1=1 — skipping make check"
    return 0
  fi
  echo "--- M1: make check ---"
  make -C "$MYALGO2_ROOT" check
}

myalgo2_run_m2_status() {
  echo "--- M2: account status ---"
  "$PYTHON" scripts/status.py --market "$MARKET"
}

myalgo2_run_m2_strategies() {
  echo "--- M2: paper strategies (daily, once) ---"
  local strategy
  for strategy in "${TIER1_STRATEGIES[@]}"; do
    echo ">>> run_paper: $strategy"
    "$PYTHON" scripts/run_paper.py \
      --strategy "$strategy" \
      --mode daily \
      --market "$MARKET" \
      --once \
      --log-level INFO
  done
}

myalgo2_run_journal_eod() {
  echo "--- Journal: EOD snapshot + sync ---"
  "$PYTHON" scripts/snapshot_account.py --type eod --market "$MARKET"
  "$PYTHON" scripts/sync_fills.py
}

myalgo2_run_report() {
  local period="$1"
  echo "--- Report: $period ---"
  "$PYTHON" scripts/report.py --period "$period"
  local stamp
  stamp="$(date +%Y%m%d)"
  "$PYTHON" scripts/report.py --period "$period" --export json \
    > "${REPORT_DIR}/report_${period}_${stamp}.json"
  echo "JSON saved: ${REPORT_DIR}/report_${period}_${stamp}.json"
}
