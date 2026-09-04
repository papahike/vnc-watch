#!/usr/bin/env bash
set -euo pipefail

prompt="${1:-Введите пароль sudo для запуска VNC Watch}"

if command -v zenity >/dev/null 2>&1; then
  exec zenity \
    --password \
    --title="VNC Watch — sudo" \
    --text="$prompt"
fi

if command -v yad >/dev/null 2>&1; then
  exec yad \
    --entry \
    --hide-text \
    --title="VNC Watch — sudo" \
    --text="$prompt" \
    --button="Отмена:1" \
    --button="OK:0"
fi

printf 'Для графического ввода пароля требуется zenity или yad.\n' >&2
exit 1
