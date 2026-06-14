#!/bin/bash
# Inject project context at session start for agents.
echo '{
  "additional_context": "myAlgo2 trading agent project. Read AGENTS.md and TASKS.md first. Default to SIMULATE trading. Run make check before finishing code changes."
}'
exit 0
