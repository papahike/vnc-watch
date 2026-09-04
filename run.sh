#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
LOG_DIR="$SCRIPT_DIR/logs"
START_LOG="$LOG_DIR/tray-start.log"
SUDO_BIN="/usr/bin/sudo"
JOURNALCTL_BIN="/usr/bin/journalctl"
PYTHON_BIN="/usr/bin/python3"
ASKPASS_BIN="$SCRIPT_DIR/sudo-askpass.sh"

AUTH_MODE="graphical"
if [[ "${1:-}" == "--terminal-auth" ]]; then
  AUTH_MODE="terminal"
  shift
fi

if [[ $# -ne 0 ]]; then
  printf 'Использование: %s [--terminal-auth]\n' "$0" >&2
  exit 2
fi

cd "$SCRIPT_DIR"

mkdir -p "$LOG_DIR"

notify_user() {
  if command -v notify-send >/dev/null 2>&1; then
    notify-send "$1" "$2" || true
  fi
}

for required_file in "$SUDO_BIN" "$JOURNALCTL_BIN" "$PYTHON_BIN"; do
  if [[ ! -x "$required_file" ]]; then
    message="Не найден обязательный файл: $required_file"
    printf '%s\n' "$message" >&2
    notify_user "VNC Watch: запуск невозможен" "$message"
    exit 1
  fi
done

if [[ "$AUTH_MODE" == "graphical" && ! -x "$ASKPASS_BIN" ]]; then
  message="Не найден графический помощник sudo: $ASKPASS_BIN"
  printf '%s\n' "$message" >&2
  notify_user "VNC Watch: запуск невозможен" "$message"
  exit 1
fi

if pgrep -f "$SCRIPT_DIR/vnc_tray.py --stdin" >/dev/null 2>&1; then
  notify_user "VNC Watch" "Мониторинг уже запущен"
  echo "Мониторинг уже запущен."
  exit 0
fi

printf '%s Запрошен ручной запуск через sudo (%s)\n' \
  "$(date --iso-8601=seconds)" "$AUTH_MODE" >"$START_LOG"

sudo_args=(-k)
if [[ "$AUTH_MODE" == "graphical" ]]; then
  export SUDO_ASKPASS="$ASKPASS_BIN"
  sudo_args+=(-A)
  notify_user \
    "VNC Watch" \
    "Введите пароль текущего пользователя в окне sudo"
else
  echo "Введите пароль текущего пользователя sudo в терминале."
fi

# Only the fixed system journal reader is elevated. The Python application,
# its history file and the whole project directory stay under the desktop user.
set +e
"$SUDO_BIN" "${sudo_args[@]}" -- \
  "$JOURNALCTL_BIN" \
  -q \
  -u x11vnc \
  -f \
  -n 0 \
  --no-pager \
  --output short-iso \
  2>>"$START_LOG" \
  | "$PYTHON_BIN" "$SCRIPT_DIR/vnc_tray.py" --stdin >>"$START_LOG" 2>&1
pipeline_status=("${PIPESTATUS[@]}")
set -e

sudo_status="${pipeline_status[0]:-1}"
tray_status="${pipeline_status[1]:-1}"
printf '%s Мониторинг завершён: sudo=%s tray=%s\n' \
  "$(date --iso-8601=seconds)" "$sudo_status" "$tray_status" >>"$START_LOG"

if [[ "$sudo_status" -ne 0 ]]; then
  message="Авторизация sudo отменена или завершилась ошибкой."
  printf '%s\n' "$message" >&2
  notify_user "VNC Watch" "$message"
  exit "$sudo_status"
fi

# Exit code 0 from the tray means that the user selected "Выход".
if [[ "$tray_status" -eq 0 ]]; then
  exit 0
fi

message="Мониторинг остановлен из-за ошибки. Подробности: $START_LOG"
printf '%s\n' "$message" >&2
notify_user "VNC Watch" "$message"
exit 1
