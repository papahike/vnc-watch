#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

check_command() {
  local name="$1"
  if ! command -v "$name" >/dev/null 2>&1; then
    echo "Внимание: не найдена команда '$name'."
    return 1
  fi
  return 0
}

chmod +x \
  setup.sh \
  build-installer.sh \
  run.sh \
  tail-log.sh \
  launch-monitor.sh \
  launch-log.sh \
  pkexec-journalctl.sh \
  install-desktop-launcher.sh \
  vnc-watch.desktop \
  show-log.desktop \
  vnc_watch.py \
  vnc_tray.py \
  show_log.py

MISSING=0
for cmd in bash python3 journalctl pkexec mkfifo; do
  check_command "$cmd" || MISSING=1
done

if ! command -v notify-send >/dev/null 2>&1; then
  echo "Внимание: notify-send не найден. Уведомления могут не показываться."
fi

./install-desktop-launcher.sh

echo
echo "Готово."
echo "Проект подготовлен к запуску в: $SCRIPT_DIR"
echo
echo "Что дальше:"
echo "1. Запустите ярлык 'Мониторинг VNC' на рабочем столе"
echo "2. Или вручную выполните: $SCRIPT_DIR/launch-monitor.sh"
echo "3. Для просмотра истории используйте ярлык 'Лог VNC'"
if [[ $MISSING -ne 0 ]]; then
  echo
  echo "Есть отсутствующие зависимости. Проверьте предупреждения выше."
fi
