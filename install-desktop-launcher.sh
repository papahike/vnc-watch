#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

detect_desktop_dir() {
  if [[ -n "${XDG_DESKTOP_DIR:-}" ]]; then
    printf '%s\n' "$XDG_DESKTOP_DIR"
    return
  fi

  if command -v xdg-user-dir >/dev/null 2>&1; then
    local xdg_dir
    xdg_dir="$(xdg-user-dir DESKTOP 2>/dev/null || true)"
    if [[ -n "$xdg_dir" && "$xdg_dir" != "$HOME" ]]; then
      printf '%s\n' "$xdg_dir"
      return
    fi
  fi

  if [[ -d "$HOME/Рабочий стол" ]]; then
    printf '%s\n' "$HOME/Рабочий стол"
    return
  fi

  if [[ -d "$HOME/Desktop" ]]; then
    printf '%s\n' "$HOME/Desktop"
    return
  fi

  printf '%s\n' "$HOME"
}

DESKTOP_DIR="$(detect_desktop_dir)"
WATCH_LAUNCHER_PATH="$DESKTOP_DIR/vnc-watch.desktop"
LOG_LAUNCHER_PATH="$DESKTOP_DIR/vnc-watch-log.desktop"

mkdir -p "$DESKTOP_DIR"

cat >"$WATCH_LAUNCHER_PATH" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Мониторинг VNC
Comment=Следить за подключениями x11vnc и показывать уведомления
Terminal=true
Exec=/bin/bash -lc 'cd "$SCRIPT_DIR" && exec ./launch-monitor.sh'
Icon=utilities-terminal
Categories=Utility;Monitor;
EOF

cat >"$LOG_LAUNCHER_PATH" <<EOF
[Desktop Entry]
Version=1.0
Type=Application
Name=Лог VNC
Comment=Показать последние события VNC
Terminal=true
Exec=/bin/bash -lc 'cd "$SCRIPT_DIR" && exec ./launch-log.sh'
Icon=text-x-log
Categories=Utility;Monitor;
EOF

chmod +x "$WATCH_LAUNCHER_PATH" "$LOG_LAUNCHER_PATH"

echo "Launchers created:"
echo "  $WATCH_LAUNCHER_PATH"
echo "  $LOG_LAUNCHER_PATH"
echo
echo "If MATE/Caja still opens it as text, right-click the file and choose:"
echo "  Allow Launching"
echo "Or open Caja preferences -> Behavior -> Executable Text Files -> Ask or Run."
