#!/bin/bash
# Warn or ask before potentially dangerous live-trading shell commands.
input=$(cat)
command=$(echo "$input" | jq -r '.command // empty')

# Allow if explicit --confirm is present
if echo "$command" | grep -q '\-\-confirm'; then
  echo '{ "permission": "allow" }'
  exit 0
fi

# Block run_live without --confirm
if echo "$command" | grep -qE 'run_live\.py'; then
  echo '{
    "permission": "ask",
    "user_message": "run_live.py places REAL orders. Use --confirm and verify FUTU_TRADE_PASSWORD is set.",
    "agent_message": "Live trading command blocked until user confirms. Prefer run_paper.py for simulation."
  }'
  exit 0
fi

# Warn on --env real without --confirm
if echo "$command" | grep -qE '\-\-env real' && ! echo "$command" | grep -q '\-\-confirm'; then
  echo '{
    "permission": "ask",
    "user_message": "Real trading env requested without --confirm. Approve only if intentional.",
    "agent_message": "Flagged --env real without --confirm."
  }'
  exit 0
fi

echo '{ "permission": "allow" }'
exit 0
