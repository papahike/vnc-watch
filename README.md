# VNC Watch

VNC Watch отслеживает журнал службы `x11vnc`, показывает уведомления о
подключениях и сохраняет историю событий в `logs/events.jsonl`. Проект
рассчитан на пользовательский графический сеанс GNOME или MATE в Linux.

VNC Watch monitors the `x11vnc` systemd journal, displays desktop notifications
and keeps a local JSONL connection history. The current launchers target GNOME
and MATE user sessions.

## Что распознаётся

- попытка входящего соединения;
- неверный пароль;
- успешное установление сессии;
- отключение клиента.

## Безопасная схема запуска

При ручном запуске графический Zenity/Yad-диалог запрашивает пароль текущего
пользователя, которому разрешён `sudo`. С повышенными правами запускается
только фиксированная команда чтения системного журнала:

```text
/usr/bin/sudo -k -A -- /usr/bin/journalctl -u x11vnc ...
                                      |
                                      +--> /usr/bin/python3 vnc_tray.py --stdin
                                           (обычный пользователь)
```

GTK-интерфейс, история и остальные файлы проекта не работают от root. Пароль
не сохраняется: askpass-помощник передаёт его непосредственно процессу `sudo`.

После входа в GNOME/MATE `autostart.sh` запускает мониторинг без пароля и без
`sudo`. Для этого у пользователя уже должен быть прямой доступ к журналу
`x11vnc`. Скрипт проверяет реальный доступ через `journalctl` и делает до трёх
повторных запусков при неожиданном завершении.

## Требования

- Linux с systemd и службой `x11vnc`;
- `/usr/bin/journalctl`, `/usr/bin/sudo` и `/usr/bin/python3`;
- Python GTK 3, PyGObject и libnotify;
- AppIndicator3 для видимой tray-иконки в GNOME (есть GTK fallback);
- Zenity или Yad для графического запроса sudo-пароля;
- GNOME или MATE;
- право текущего пользователя запускать `sudo` для ручного режима.

Для фонового режима администратор может выдать доступ через группу
`systemd-journal` или эквивалентный ACL. После изменения групп нужно полностью
выйти из графического сеанса и войти снова.

Быстрая проверка зависимостей:

```bash
test -x /usr/bin/sudo
test -x /usr/bin/journalctl
test -x /usr/bin/python3
command -v zenity || command -v yad
/usr/bin/journalctl -q -u x11vnc -n 1 --no-pager
/usr/bin/python3 -c 'import gi; gi.require_version("Gtk", "3.0"); gi.require_version("Notify", "0.7")'
```

## Установка из папки проекта

```bash
git clone https://github.com/papahike/vnc-watch.git
cd vnc-watch
git switch feature/vnc-watch-installer
./setup.sh
```

Установщик создаст на рабочем столе ярлыки `Мониторинг VNC`, `Лог VNC` и
файл автозапуска `~/.config/autostart/vnc-watch.desktop`. В GNOME он также
попытается включить уже установленное расширение AppIndicator.

## Переносимый установщик

```bash
./build-installer.sh
```

Готовый файл появится в `dist/vnc-watch-installer.run`. На другом компьютере:

```bash
chmod +x vnc-watch-installer.run
./vnc-watch-installer.run
```

По умолчанию установка выполняется в `~/vnc-watch`; другой каталог можно
передать первым аргументом. Короткая памятка находится в
[`NOTEBOOK_QUICKSTART_RU.md`](NOTEBOOK_QUICKSTART_RU.md).

## Использование и диагностика

Ручной графический запуск:

```bash
./run.sh
```

Диагностический запуск с вводом sudo-пароля в терминале:

```bash
./launch-monitor.sh
```

Запуск фонового режима в текущем графическом сеансе:

```bash
./autostart.sh
```

Просмотр истории:

```bash
./tail-log.sh
```

Диагностика записывается в `logs/tray-start.log` и `logs/autostart.log`.
Повторный запуск не создаёт вторую tray-иконку. Пункт меню `Выход` завершает
мониторинг без автоматического перезапуска.

Если tray-библиотеки или расширения GNOME AppIndicator нет, уведомления могут
продолжить работать через GTK fallback, но значок оболочка может не показать.

## Обновление со старой версии

В актуальной версии больше не используются `pkexec-journalctl.sh` и
`vnc-watch.service`. Если старый user-service ранее включался вручную,
остановите его перед запуском новой версии:

```bash
systemctl --user disable --now vnc-watch.service
systemctl --user daemon-reload
```

Затем обновите файлы и снова выполните `./setup.sh`.

## Основные файлы

- `run.sh` и `sudo-askpass.sh` — ручной запуск через sudo;
- `autostart.sh` — беспарольный запуск в пользовательском сеансе;
- `vnc_tray.py` — GTK-интерфейс, tray-иконка и уведомления;
- `install-desktop-launcher.sh` — установка ярлыков и автозапуска;
- `setup.sh` и `build-installer.sh` — переносимая установка;
- `show_log.py` и `tail-log.sh` — просмотр истории;
- `tests/` — автоматические проверки.
