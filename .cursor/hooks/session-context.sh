#!/bin/bash
# Inject project context at session start for agents.
echo '{
  "additional_context": "myAlgo2: ALL transactions MUST use Futu paper/simulate account (trading.paper_only: true). Never run run_live.py or --env real until user explicitly says to switch. Use run_paper.py. Read AGENTS.md and TASKS.md."
}'
exit 0
