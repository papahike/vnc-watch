#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"

chmod +x \
  setup.sh \
  build-installer.sh \
  run.sh \
  sudo-askpass.sh \
  autostart.sh \
  tail-log.sh \
  launch-monitor.sh \
  launch-log.sh \
  install-desktop-launcher.sh \
  vnc-watch.desktop \
  show-log.desktop \
  vnc-watch-autostart.desktop

missing=0
for required_file in /usr/bin/sudo /usr/bin/journalctl /usr/bin/python3; do
  if [[ ! -x "$required_file" ]]; then
    echo "Не найден обязательный файл: $required_file" >&2
    missing=1
  fi
done

if ! command -v zenity >/dev/null 2>&1 \
  && ! command -v yad >/dev/null 2>&1; then
  echo "Не найден zenity или yad: графический запрос sudo-пароля недоступен." >&2
  missing=1
fi

if [[ -x /usr/bin/python3 ]] \
  && ! /usr/bin/python3 -c \
    'import gi; gi.require_version("Gtk", "3.0"); gi.require_version("Notify", "0.7")' \
    >/dev/null 2>&1; then
  echo "Не найдены Python GTK 3 / PyGObject / libnotify." >&2
  missing=1
fi

if [[ "$missing" -ne 0 ]]; then
  echo "Установите отсутствующие зависимости и повторите ./setup.sh" >&2
  exit 1
fi

./install-desktop-launcher.sh

echo
echo "Готово. VNC Watch установлен из: $SCRIPT_DIR"
echo "Фоновый режим запустится после следующего входа в GNOME/MATE."
echo "Для ручной проверки откройте ярлык «Мониторинг VNC»."
