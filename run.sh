#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
START_LOG="$LOG_DIR/tray-start.log"
MODE_FILE="$LOG_DIR/mode.txt"
ACCESS_FILE="$LOG_DIR/access-mode.txt"
PIPE_PATH="$LOG_DIR/journal.pipe"
WATCHER_LOG="$LOG_DIR/watcher.log"

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

wait_for_start() {
  local pattern="$1"
  local seconds=20

  while (( seconds > 0 )); do
    if pgrep -f "$pattern" >/dev/null 2>&1; then
      return 0
    fi
    sleep 1
    ((seconds--))
  done

  return 1
}

prepare_pipe() {
  if [[ -e "$PIPE_PATH" && ! -p "$PIPE_PATH" ]]; then
    rm -f "$PIPE_PATH"
  fi
  if [[ ! -p "$PIPE_PATH" ]]; then
    mkfifo "$PIPE_PATH"
  fi
}

start_watcher() {
  local watcher_target="$1"
  : >"$WATCHER_LOG"

  nohup env SCRIPT_DIR="$SCRIPT_DIR" PIPE_PATH="$PIPE_PATH" bash -lc "
    cat \"\$PIPE_PATH\" | python3 \"$watcher_target\" $2
  " >>"$WATCHER_LOG" 2>&1 </dev/null &
}

start_privileged_reader() {
  if ! command -v pkexec >/dev/null 2>&1; then
    echo "Команда pkexec не найдена."
    return 1
  fi

  printf 'pkexec\n' >"$ACCESS_FILE"
  pkexec "$SCRIPT_DIR/pkexec-journalctl.sh"
}

show_access_error() {
  echo "Не удалось получить доступ к журналу x11vnc через polkit."
  echo "Что проверить:"
  echo "1. Есть ли на машине pkexec и polkit-agent."
  echo "2. Появляется ли графический запрос пароля администратора."
  echo "3. Разрешено ли через polkit запускать journalctl от root."
  echo "4. Если polkit в вашей сети не используется, настройте sudoers для этого пользователя."
  if [[ -f "$START_LOG" ]]; then
    echo
    echo "Последние строки лога запуска:"
    tail -n 20 "$START_LOG" || true
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

: >"$START_LOG"
prepare_pipe

if supports_tray; then
  printf 'tray\n' >"$MODE_FILE"
  start_watcher "$SCRIPT_DIR/vnc_tray.py" "--stdin"
  if ! wait_for_start "$SCRIPT_DIR/vnc_tray.py --stdin"; then
    echo "Не удалось запустить tray watcher."
    tail -n 20 "$WATCHER_LOG" || true
    exit 1
  fi
  if ! start_privileged_reader; then
    show_access_error
    exit 1
  fi
else
  printf 'notify-only\n' >"$MODE_FILE"
  start_watcher "$SCRIPT_DIR/vnc_watch.py" "--notify --stdin"
  if ! wait_for_start "$SCRIPT_DIR/vnc_watch.py --notify --stdin"; then
    echo "Не удалось запустить фоновый watcher."
    tail -n 20 "$WATCHER_LOG" || true
    exit 1
  fi
  if ! start_privileged_reader; then
    show_access_error
    exit 1
  fi
fi

sleep 1

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
if [[ -f "$ACCESS_FILE" ]]; then
  echo "Доступ к журналу: $(cat "$ACCESS_FILE")"
fi
if [[ -f "$WATCHER_LOG" ]]; then
  echo "Лог watcher: $WATCHER_LOG"
fi
tail -n 20 "$START_LOG" || true
exit 1
