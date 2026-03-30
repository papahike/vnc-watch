# vnc-watch

Small watcher for `x11vnc` on RedOS.

It follows `journalctl -u x11vnc -f`, extracts useful events, writes them to a
local JSONL history file, and can show desktop notifications with
`notify-send`.

## Description RU

`vnc-watch` helps answer questions like:

- кто подключался к моему ПК
- кто подключался по удаленке
- как посмотреть подключения к компьютеру
- как узнать кто заходил через VNC
- как отследить удаленные подключения к рабочему ПК
- Remmina мониторинг подключений
- аудит удаленного доступа на RedOS

Проект ориентирован на `RedOS` и `x11vnc`/`VNC`. Он показывает входящие
подключения к рабочему столу, ошибки аутентификации, успешные сессии и
отключения клиентов. Полезен для сценариев с `Remmina`, локальной сетью,
корпоративной сетью и общим мониторингом удаленного доступа. Из коробки
проект мониторит `VNC/x11vnc`; для `RDP/xrdp` его можно адаптировать под
другой источник журналов.

## Description EN

`vnc-watch` is a lightweight remote desktop connection monitor for `RedOS`
systems using `x11vnc`. It helps answer questions such as:

- who connected to my computer
- who connected remotely to my PC
- how to see who connected over VNC
- how to monitor Remmina remote desktop sessions
- how to audit remote desktop access on Linux
- how to track incoming VNC connections

The tool watches `x11vnc` logs, records connection attempts, failed
authentication, successful VNC sessions, and disconnects. It is useful for
remote access auditing, workstation monitoring, and notification-based tracking
of incoming desktop sessions. The current implementation targets `VNC/x11vnc`;
`RDP/xrdp` support would require a different log source.

## Search Keywords

Russian:
- кто подключался к пк
- кто подключался к моему компьютеру
- кто подключался по удаленке
- посмотреть удаленные подключения
- журнал удаленных подключений linux
- журнал подключений remmina
- мониторинг vnc redos
- мониторинг удаленного рабочего стола
- аудит подключений vnc
- remmina vnc лог подключений

English:
- who connected to my pc
- who connected remotely to my computer
- VNC connection monitor Linux
- Remmina connection monitor
- remote desktop access audit
- x11vnc session monitor
- VNC login notifications
- remote support connection history
- desktop sharing audit log
- RedOS VNC monitoring

## What it detects

- incoming connection attempt
- wrong password
- successful session establishment
- client disconnect

## Files

- `vnc_watch.py`: main watcher
- `run.sh`: start watcher and request privileged journal access through `pkexec`
- `launch-monitor.sh`: open terminal and start monitoring interactively
- `launch-log.sh`: open terminal and show readable history
- `pkexec-journalctl.sh`: privileged helper started through polkit
- `setup.sh`: one-step bootstrap for another machine
- `build-installer.sh`: build a self-extracting `.run` installer
- `NOTEBOOK_QUICKSTART_RU.md`: short Russian checklist for laptop rollout
- `vnc_tray.py`: GTK tray app with notifications and recent events menu
- `show_log.py`: human-readable history viewer
- `tail-log.sh`: show the latest parsed events in readable form
- `vnc-watch.desktop`: launcher for double-click start from file manager
- `show-log.desktop`: launcher for viewing the last events
- `install-desktop-launcher.sh`: create a desktop launcher with absolute paths
- `vnc-watch.service`: example user-level systemd unit
- `logs/events.jsonl`: event history created at runtime

## Run manually

Or just run:

```bash
cd /root/projects/vnc-watch
./run.sh
```

`run.sh` starts the watcher and then requests privileged access to `journalctl`
through `pkexec`. A graphical administrator password prompt is expected on
machines where direct journal access is restricted.

If tray startup fails, inspect:

```bash
tail -n 50 /root/projects/vnc-watch/logs/tray-start.log
```

If GTK tray support is unavailable on the target machine, `run.sh` falls back
to a background watcher without tray icon and keeps desktop notifications.

To create a launcher on the desktop with absolute paths:

```bash
cd /root/projects/vnc-watch
./install-desktop-launcher.sh
```

## Install On Another Machine

If you copy the whole `vnc-watch` folder to another RedOS machine, one command
is enough:

```bash
cd /path/to/vnc-watch
chmod +x setup.sh
./setup.sh
```

`setup.sh` will:

- mark all required scripts as executable
- detect the current desktop directory
- create desktop launchers
- print the next steps

## Build Single-File Installer

To build one portable installer file:

```bash
cd /root/projects/vnc-watch
./build-installer.sh
```

The result will be:

```bash
/root/projects/vnc-watch/dist/vnc-watch-installer.run
```

On another machine:

```bash
chmod +x vnc-watch-installer.run
./vnc-watch-installer.run /path/to/install/vnc-watch
```

This creates two desktop launchers:

- `vnc-watch.desktop`: start monitoring
- `vnc-watch-log.desktop`: show the latest parsed events

## Show recent parsed events

```bash
tail -n 50 /root/projects/vnc-watch/logs/events.jsonl
```

Or:

```bash
cd /root/projects/vnc-watch
./tail-log.sh
```

## Example user service

The bundled unit expects the project to live in `%h/project/vnc-watch` on the
target machine. If you keep it elsewhere, adjust `WorkingDirectory` and
`ExecStart`.

Copy the project into your home directory on the target machine, then install
the unit:

```bash
mkdir -p ~/project
cp -r /root/projects/vnc-watch ~/project/
mkdir -p ~/.config/systemd/user
cp ~/project/vnc-watch/vnc-watch.service ~/.config/systemd/user/
systemctl --user daemon-reload
systemctl --user enable --now vnc-watch.service
```

## Notes

- Desktop notifications work only if the service runs in a user graphical
  session with access to `DBUS_SESSION_BUS_ADDRESS`.
- History starts from the moment the watcher is launched; it does not rebuild
  old sessions from archived logs.
- If your file manager allows launching executable files, you can double-click
  `vnc-watch.desktop` or `run.sh`. For desktop launchers you may need to mark
  the file as trusted the first time.
- In MATE/Caja, `.sh` files may open as text until you change Preferences ->
  Behavior -> Executable Text Files to `Ask each time` or `Run executable text
  files when they are opened`.
