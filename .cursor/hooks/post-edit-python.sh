#!/bin/bash
# Optional: run ruff on edited Python files if ruff is available.
input=$(cat)
file_path=$(echo "$input" | jq -r '.file_path // .path // empty')

if [[ -z "$file_path" || ! "$file_path" =~ \.py$ ]]; then
  exit 0
fi

if command -v ruff >/dev/null 2>&1; then
  ruff check --fix "$file_path" 2>/dev/null || true
fi

exit 0
