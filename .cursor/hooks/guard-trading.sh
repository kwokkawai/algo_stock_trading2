#!/bin/bash
# Block live trading while paper_only policy is in effect.
input=$(cat)
command=$(echo "$input" | jq -r '.command // empty')

# Always block run_live.py (real trading script)
if echo "$command" | grep -qE 'run_live\.py'; then
  echo '{
    "permission": "deny",
    "user_message": "run_live.py is disabled. All trading must use the Futu paper account via run_paper.py until you explicitly switch paper_only off.",
    "agent_message": "Do not run run_live.py. User requires paper-only trading. Use run_paper.py or run_tick.py."
  }'
  exit 0
fi

# Block any CLI attempt to use --env real
if echo "$command" | grep -qE '\-\-env[ =]real|\-\-env=real'; then
  echo '{
    "permission": "deny",
    "user_message": "Real trading (--env real) is disabled. Use paper/simulate account only.",
    "agent_message": "Never pass --env real. trading.paper_only is true in config."
  }'
  exit 0
fi

echo '{ "permission": "allow" }'
exit 0
