#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
START_LOG="$LOG_DIR/autostart.log"
JOURNALCTL_BIN="/usr/bin/journalctl"
PYTHON_BIN="/usr/bin/python3"
MAX_RESTARTS=3
RESTART_DELAY_SECONDS=3
STABLE_RUN_SECONDS=60

mkdir -p "$LOG_DIR"
exec >>"$START_LOG" 2>&1

printf '%s VNC Watch autostart requested\n' "$(date --iso-8601=seconds)"

notify_user() {
  if command -v notify-send >/dev/null 2>&1; then
    notify-send "$1" "$2" || true
  fi
}

for required_file in "$JOURNALCTL_BIN" "$PYTHON_BIN"; do
  if [[ ! -x "$required_file" ]]; then
    message="Не найден обязательный файл: $required_file"
    printf '%s %s\n' "$(date --iso-8601=seconds)" "$message"
    notify_user "VNC Watch: автозапуск невозможен" "$message"
    exit 1
  fi
done

if pgrep -f "$SCRIPT_DIR/vnc_tray.py --stdin" >/dev/null 2>&1; then
  printf '%s VNC Watch is already running\n' "$(date --iso-8601=seconds)"
  exit 0
fi

if ! "$JOURNALCTL_BIN" -q -u x11vnc -n 1 --no-pager >/dev/null 2>&1; then
  message="Нет доступа к журналу x11vnc. Запустите ручную диагностику VNC Watch."
  printf '%s %s\n' "$(date --iso-8601=seconds)" "$message"
  notify_user "VNC Watch: автозапуск не выполнен" "$message"
  exit 1
fi

restart_count=0
while true; do
  started_at="$(date +%s)"

  set +e
  "$JOURNALCTL_BIN" \
    -q \
    -u x11vnc \
    -f \
    -n 0 \
    --no-pager \
    --output short-iso \
    | "$PYTHON_BIN" "$SCRIPT_DIR/vnc_tray.py" --stdin
  pipeline_status=("${PIPESTATUS[@]}")
  set -e

  journal_status="${pipeline_status[0]:-1}"
  tray_status="${pipeline_status[1]:-1}"
  printf '%s VNC Watch stopped: journalctl=%s tray=%s\n' \
    "$(date --iso-8601=seconds)" "$journal_status" "$tray_status"

  if [[ "$tray_status" -eq 0 ]]; then
    printf '%s VNC Watch stopped by user\n' "$(date --iso-8601=seconds)"
    exit 0
  fi

  runtime_seconds=$(( $(date +%s) - started_at ))
  if (( runtime_seconds >= STABLE_RUN_SECONDS )); then
    restart_count=0
  fi
  restart_count=$((restart_count + 1))

  if (( restart_count > MAX_RESTARTS )); then
    message="Мониторинг несколько раз аварийно остановился. Проверьте $START_LOG"
    printf '%s %s\n' "$(date --iso-8601=seconds)" "$message"
    notify_user "VNC Watch остановлен" "$message"
    exit 1
  fi

  if ! "$JOURNALCTL_BIN" -q -u x11vnc -n 1 --no-pager >/dev/null 2>&1; then
    message="После остановки утрачен доступ к журналу x11vnc."
    printf '%s %s\n' "$(date --iso-8601=seconds)" "$message"
    notify_user "VNC Watch остановлен" "$message"
    exit 1
  fi

  printf '%s Перезапуск VNC Watch через %s с (попытка %s/%s)\n' \
    "$(date --iso-8601=seconds)" "$RESTART_DELAY_SECONDS" \
    "$restart_count" "$MAX_RESTARTS"
  sleep "$RESTART_DELAY_SECONDS"
done
