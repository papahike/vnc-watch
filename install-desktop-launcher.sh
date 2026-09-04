#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

if [[ -n "${XDG_DESKTOP_DIR:-}" ]]; then
  DESKTOP_DIR="$XDG_DESKTOP_DIR"
elif command -v xdg-user-dir >/dev/null 2>&1; then
  DESKTOP_DIR="$(xdg-user-dir DESKTOP)"
elif [[ -d "$HOME/Рабочий стол" ]]; then
  DESKTOP_DIR="$HOME/Рабочий стол"
else
  DESKTOP_DIR="$HOME/Desktop"
fi

WATCH_LAUNCHER_PATH="$DESKTOP_DIR/vnc-watch.desktop"
LOG_LAUNCHER_PATH="$DESKTOP_DIR/vnc-watch-log.desktop"
AUTOSTART_DIR="${XDG_CONFIG_HOME:-$HOME/.config}/autostart"
AUTOSTART_PATH="$AUTOSTART_DIR/vnc-watch.desktop"

mkdir -p "$DESKTOP_DIR" "$AUTOSTART_DIR"
chmod +x \
  "$SCRIPT_DIR/run.sh" \
  "$SCRIPT_DIR/sudo-askpass.sh" \
  "$SCRIPT_DIR/autostart.sh" \
  "$SCRIPT_DIR/launch-monitor.sh" \
  "$SCRIPT_DIR/launch-log.sh" \
  "$SCRIPT_DIR/tail-log.sh"

cat >"$WATCH_LAUNCHER_PATH" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Мониторинг VNC
Comment=Запустить мониторинг с паролем текущего sudo-пользователя
Terminal=false
Exec=/bin/bash "$SCRIPT_DIR/run.sh"
Icon=network-server
Categories=System;Monitor;
EOF

cat >"$LOG_LAUNCHER_PATH" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Лог VNC
Comment=Показать последние события VNC
Terminal=true
Exec=/bin/bash "$SCRIPT_DIR/launch-log.sh"
Icon=text-x-log
Categories=System;Monitor;
EOF

cat >"$AUTOSTART_PATH" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=VNC Watch
Comment=Автоматически следить за подключениями x11vnc
Exec=/bin/bash "$SCRIPT_DIR/autostart.sh"
Icon=network-idle
Terminal=false
X-GNOME-Autostart-enabled=true
X-MATE-Autostart-Delay=5
EOF

chmod +x "$WATCH_LAUNCHER_PATH" "$LOG_LAUNCHER_PATH"
chmod 0644 "$AUTOSTART_PATH"

APPINDICATOR_EXTENSION="appindicatorsupport@rgcjonas.gmail.com"
if [[ "${XDG_CURRENT_DESKTOP:-}" == *GNOME* ]] \
  && command -v gnome-extensions >/dev/null 2>&1 \
  && gnome-extensions list 2>/dev/null | grep -Fxq "$APPINDICATOR_EXTENSION"; then
  if ! gnome-extensions enable "$APPINDICATOR_EXTENSION"; then
    echo "Предупреждение: не удалось включить расширение GNOME AppIndicator." >&2
  fi
fi

echo "Ярлыки и автозапуск созданы:"
echo "  $WATCH_LAUNCHER_PATH"
echo "  $LOG_LAUNCHER_PATH"
echo "  $AUTOSTART_PATH"
echo "Если файловый менеджер открывает ярлык как текст, щёлкните по нему правой"
echo "кнопкой мыши и выберите «Разрешить запуск» или «Allow Launching»."
