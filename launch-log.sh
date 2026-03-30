#!/usr/bin/env bash
set -uo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"

cd "$SCRIPT_DIR"
STATUS=0
./tail-log.sh || STATUS=$?
echo
if [[ $STATUS -ne 0 ]]; then
  echo "Не удалось открыть лог. Код завершения: $STATUS"
fi
echo 'Нажмите любую клавишу для закрытия окна...'
read -n 1 -s -r
