#!/usr/bin/env bash
# Install macOS launchd agents for myAlgo2 scheduled jobs.
#
# Usage:
#   ./scripts/install_launchd.sh          # install + load
#   ./scripts/install_launchd.sh uninstall

set -euo pipefail

ROOT="$(cd "$(dirname "$0")/.." && pwd)"
PLIST_SRC="${ROOT}/launchd"
AGENTS_DIR="${HOME}/Library/LaunchAgents"
LABELS=(
  com.myalgo2.daily
  com.myalgo2.weekly-report
  com.myalgo2.monthly-report
)

install_plists() {
  mkdir -p "$AGENTS_DIR"
  for label in "${LABELS[@]}"; do
    src="${PLIST_SRC}/${label}.plist"
    dst="${AGENTS_DIR}/${label}.plist"
    if [[ ! -f "$src" ]]; then
      echo "ERROR: missing $src"
      exit 1
    fi
    sed "s|@PROJECT_ROOT@|${ROOT}|g" "$src" > "$dst"
    echo "Installed $dst"
    launchctl bootout "gui/$(id -u)/${label}" 2>/dev/null || \
      launchctl unload "$dst" 2>/dev/null || true
    launchctl bootstrap "gui/$(id -u)" "$dst" 2>/dev/null || \
      launchctl load "$dst"
    echo "Loaded $label"
  done
  echo ""
  echo "Done. Schedules (macOS local timezone):"
  echo "  daily_run.sh       Mon–Fri 16:30"
  echo "  weekly_report.sh   Sun      18:00"
  echo "  monthly_report.sh  1st      09:00"
  echo ""
  echo "Ensure macOS timezone is Asia/Hong_Kong, or edit plists in:"
  echo "  $AGENTS_DIR"
}

uninstall_plists() {
  for label in "${LABELS[@]}"; do
    dst="${AGENTS_DIR}/${label}.plist"
    launchctl bootout "gui/$(id -u)/${label}" 2>/dev/null || \
      launchctl unload "$dst" 2>/dev/null || true
    rm -f "$dst"
    echo "Removed $label"
  done
}

case "${1:-install}" in
  install) install_plists ;;
  uninstall) uninstall_plists ;;
  *)
    echo "Usage: $0 [install|uninstall]"
    exit 1
    ;;
esac
