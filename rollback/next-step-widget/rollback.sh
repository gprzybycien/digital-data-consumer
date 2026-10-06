#!/bin/sh
set -eu
TASK_ROOT=$(CDPATH= cd -- "$(dirname -- "$0")/../.." && pwd)
ORCHESTRATE_CLI=${ORCHESTRATE_CLI:-/Users/grzegorzprzybycien/Documents/ChatGPT/data-steward-agent/.venv/bin/orchestrate}
"$ORCHESTRATE_CLI" agents import -f "$TASK_ROOT/rollback/next-step-widget/wxdi-data-consumer.before.yaml"
"$ORCHESTRATE_CLI" agents deploy -n wxdi_data_consumer
# Tools are detached by the saved definition; leaving them installed permits re-enabling.
