#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
START_LOG="$LOG_DIR/tray-start.log"
MODE_FILE="$LOG_DIR/mode.txt"

cd "$SCRIPT_DIR"

mkdir -p "$LOG_DIR"

supports_tray() {
  [[ -n "${DISPLAY:-}" ]] || return 1
  python3 - <<'PY' >/dev/null 2>&1
import importlib.util
raise SystemExit(0 if importlib.util.find_spec("gi") else 1)
PY
}

safe_notify() {
  if command -v notify-send >/dev/null 2>&1; then
    notify-send "$@"
  fi
}

if pgrep -f "$SCRIPT_DIR/vnc_tray.py --stdin" >/dev/null 2>&1; then
  safe_notify "VNC Watch" "Мониторинг уже запущен"
  echo "Мониторинг уже запущен."
  exit 0
fi

if pgrep -f "$SCRIPT_DIR/vnc_watch.py --notify --stdin" >/dev/null 2>&1; then
  safe_notify "VNC Watch" "Мониторинг уже запущен"
  echo "Мониторинг уже запущен."
  exit 0
fi

sudo -v
: >"$START_LOG"

if supports_tray; then
  printf 'tray\n' >"$MODE_FILE"
  nohup env SCRIPT_DIR="$SCRIPT_DIR" bash -lc '
    sudo -n journalctl -u x11vnc -f -n 0 --no-pager --output short-iso \
      | python3 "$SCRIPT_DIR/vnc_tray.py" --stdin
  ' >>"$START_LOG" 2>&1 </dev/null &
else
  printf 'notify-only\n' >"$MODE_FILE"
  nohup env SCRIPT_DIR="$SCRIPT_DIR" bash -lc '
    sudo -n journalctl -u x11vnc -f -n 0 --no-pager --output short-iso \
      | python3 "$SCRIPT_DIR/vnc_watch.py" --notify --stdin
  ' >>"$START_LOG" 2>&1 </dev/null &
fi

sleep 2

if pgrep -f "$SCRIPT_DIR/vnc_tray.py --stdin" >/dev/null 2>&1; then
  safe_notify "VNC Watch" "Мониторинг запущен и свернут в трей"
  echo "Мониторинг запущен и свернут в трей."
  echo "Если иконки не видно, проверьте область уведомлений MATE."
  exit 0
fi

if pgrep -f "$SCRIPT_DIR/vnc_watch.py --notify --stdin" >/dev/null 2>&1; then
  safe_notify "VNC Watch" "Мониторинг запущен в фоновом режиме"
  echo "Мониторинг запущен в фоновом режиме без tray."
  echo "Уведомления будут приходить, но значок в трее не используется."
  exit 0
fi

echo "Не удалось запустить мониторинг."
echo "Подробности смотрите в: $START_LOG"
if [[ -f "$MODE_FILE" ]]; then
  echo "Режим запуска: $(cat "$MODE_FILE")"
fi
tail -n 20 "$START_LOG" || true
exit 1
