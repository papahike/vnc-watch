#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"
echo 'Диагностический запуск VNC Watch через sudo.'
echo 'Введите пароль текущего пользователя, добавленного в sudoers.'
echo 'Окно останется открытым, пока работает мониторинг.'
echo
STATUS=0
./run.sh --terminal-auth || STATUS=$?
echo
if [[ $STATUS -eq 0 ]]; then
  echo 'Мониторинг завершён или уже был запущен.'
else
  echo "Запуск завершился с ошибкой. Код: $STATUS"
  echo 'Если выше не видно причины, откройте logs/tray-start.log'
fi
echo 'Нажмите любую клавишу для закрытия окна...'
read -n 1 -s -r
