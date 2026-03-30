#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
PIPE_PATH="$LOG_DIR/journal.pipe"
PID_FILE="$LOG_DIR/root-journalctl.pid"
START_LOG="$LOG_DIR/tray-start.log"

mkdir -p "$LOG_DIR"

if [[ ! -p "$PIPE_PATH" ]]; then
  echo "FIFO pipe not found: $PIPE_PATH" >>"$START_LOG"
  exit 1
fi

if [[ -f "$PID_FILE" ]]; then
  OLD_PID="$(cat "$PID_FILE" 2>/dev/null || true)"
  if [[ -n "${OLD_PID:-}" ]] && kill -0 "$OLD_PID" 2>/dev/null; then
    kill "$OLD_PID" 2>/dev/null || true
    sleep 1
  fi
fi

nohup bash -lc '
  exec journalctl -u x11vnc -f -n 0 --no-pager --output short-iso >"$1"
' _ "$PIPE_PATH" >>"$START_LOG" 2>&1 </dev/null &

NEW_PID=$!
printf '%s\n' "$NEW_PID" >"$PID_FILE"
chmod 644 "$PID_FILE" 2>/dev/null || true

exit 0
