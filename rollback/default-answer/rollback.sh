#!/bin/sh
set -eu
TASK_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ORCHESTRATE_CLI=${ORCHESTRATE_CLI:-/Users/grzegorzprzybycien/Documents/ChatGPT/data-steward-agent/.venv/bin/orchestrate}
"$ORCHESTRATE_CLI" tools import -k python -f "$TASK_ROOT/rollback/default-answer/next_steps.before.py"
"$ORCHESTRATE_CLI" agents import -f "$TASK_ROOT/rollback/default-answer/wxdi-data-consumer.before.yaml"
"$ORCHESTRATE_CLI" agents deploy -n wxdi_data_consumer
