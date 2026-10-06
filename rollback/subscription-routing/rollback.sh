#!/bin/sh
set -eu
CLI=/Users/grzegorzprzybycien/Documents/ChatGPT/data-steward-agent/.venv/bin/orchestrate
ROOT=$(CDPATH= cd -- "$(dirname "$0")/../.." && pwd)
"$CLI" tools import -k python -f "$ROOT/rollback/subscription-routing/next_steps.before.py"
"$CLI" agents import -f "$ROOT/rollback/subscription-routing/wxdi-data-consumer.before.yaml"
"$CLI" agents deploy -n wxdi_data_consumer
