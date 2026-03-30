#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_FILE="$SCRIPT_DIR/logs/events.jsonl"

if [[ ! -f "$LOG_FILE" ]]; then
  echo "Лог пока пуст: $LOG_FILE"
  exit 0
fi

python3 "$SCRIPT_DIR/show_log.py"
