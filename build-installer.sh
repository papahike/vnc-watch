#!/usr/bin/env bash
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
DIST_DIR="$SCRIPT_DIR/dist"
PAYLOAD_DIR="$DIST_DIR/payload"
ARCHIVE_PATH="$DIST_DIR/vnc-watch.tar.gz"
OUTPUT_PATH="$DIST_DIR/vnc-watch-installer.run"

mkdir -p "$DIST_DIR"
rm -rf "$PAYLOAD_DIR"
mkdir -p "$PAYLOAD_DIR"

copy_file() {
  local source_path="$1"
  cp "$SCRIPT_DIR/$source_path" "$PAYLOAD_DIR/$source_path"
}

copy_file README.md
copy_file NOTEBOOK_QUICKSTART_RU.md
copy_file build-installer.sh
copy_file setup.sh
copy_file install-desktop-launcher.sh
copy_file run.sh
copy_file sudo-askpass.sh
copy_file autostart.sh
copy_file launch-monitor.sh
copy_file launch-log.sh
copy_file tail-log.sh
copy_file vnc-watch.desktop
copy_file show-log.desktop
copy_file vnc-watch-autostart.desktop
copy_file vnc_tray.py
copy_file vnc_watch.py
copy_file show_log.py
copy_file watchlib.py

tar -C "$PAYLOAD_DIR" -czf "$ARCHIVE_PATH" .

cat >"$OUTPUT_PATH" <<'EOF'
#!/usr/bin/env bash
set -euo pipefail

TARGET_DIR="${1:-$HOME/vnc-watch}"
mkdir -p "$TARGET_DIR"

ARCHIVE_LINE="$(awk '/^__ARCHIVE_BELOW__$/ {print NR + 1; exit 0;}' "$0")"
if [[ -z "${ARCHIVE_LINE:-}" ]]; then
  echo "Installer payload marker not found." >&2
  exit 1
fi

tail -n +"$ARCHIVE_LINE" "$0" | tar -xz -C "$TARGET_DIR"

cd "$TARGET_DIR"
chmod +x setup.sh
./setup.sh

echo
echo "Установка завершена: $TARGET_DIR"
exit 0
__ARCHIVE_BELOW__
EOF

cat "$ARCHIVE_PATH" >>"$OUTPUT_PATH"
chmod +x "$OUTPUT_PATH"

echo "Готовый установщик: $OUTPUT_PATH"
