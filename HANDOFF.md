# HANDOFF

## Цель

Обновить публичный репозиторий VNC Watch рабочей версией для GNOME/MATE:
ручной запуск с паролем текущего sudo-пользователя, беспарольный автозапуск
при наличии доступа к журналу и переносимая установка на другой компьютер.

## Сделано

- Локальный рабочий каталог подключён к истории ветки
  `feature/vnc-watch-installer` репозитория `papahike/vnc-watch`.
- Ручной запуск переведён с `pkexec` на `/usr/bin/sudo -k -A`; с повышенными
  правами работает только `/usr/bin/journalctl`.
- Добавлен графический askpass через Zenity с резервом на Yad и терминальный
  режим `run.sh --terminal-auth`.
- Добавлен GNOME/MATE-autostart без `sudo`, с проверкой фактического доступа к
  журналу и тремя попытками перезапуска после неожиданной остановки.
- Tray использует AppIndicator3 с резервом на `Gtk.StatusIcon`.
- Установщик создаёт два ярлыка и запись autostart, а переносимый `.run`-файл
  включает все новые скрипты.
- Удалены устаревшие `pkexec-journalctl.sh` и `vnc-watch.service`.
- Desktop-шаблоны очищены от путей конкретного компьютера.
- Обновлены README, краткая памятка, `.gitignore` и автоматические тесты.

## Изменённые области

- Запуск: `run.sh`, `sudo-askpass.sh`, `autostart.sh`, `launch-monitor.sh`.
- Установка: `setup.sh`, `build-installer.sh`,
  `install-desktop-launcher.sh` и desktop-файлы.
- Интерфейс: `vnc_tray.py`.
- Тесты: `tests/`.
- Документация: `README.md`, `NOTEBOOK_QUICKSTART_RU.md`, `HANDOFF.md`.

## Проверка

```bash
bash -n run.sh sudo-askpass.sh autostart.sh launch-monitor.sh \
  launch-log.sh tail-log.sh install-desktop-launcher.sh setup.sh \
  build-installer.sh
desktop-file-validate vnc-watch.desktop show-log.desktop \
  vnc-watch-autostart.desktop
python3 -m py_compile vnc_tray.py vnc_watch.py watchlib.py show_log.py
python3 -m pytest -q
```

Результат: 31 тест пройден; shell-, Python- и desktop-проверки успешны.
Интеграционные тесты отдельно собирают самораспаковывающийся установщик,
устанавливают его в путь с пробелами и проверяют новые ярлыки/autostart.

## Открытые риски

- Реальный ввод sudo-пароля не автоматизируется и требует ручной проверки.
- Полный перевход в GNOME/MATE и тестовое VNC-подключение не входят в
  автоматические тесты.
- Для видимой tray-иконки GNOME нужны AppIndicator3 и соответствующее
  расширение оболочки; без них остаётся GTK fallback.

## Следующий точный шаг

На втором компьютере установить свежую версию через
`dist/vnc-watch-installer.run`, выполнить одно тестовое VNC-подключение и
проверить уведомление, tray-меню и новую строку в `logs/events.jsonl`.
