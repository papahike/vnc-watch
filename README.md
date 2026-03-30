# vnc-watch

Small watcher for `x11vnc` on RedOS.

It follows `journalctl -u x11vnc -f`, extracts useful events, writes them to a
local JSONL history file, and can show desktop notifications with
`notify-send`.

## What it detects

- incoming connection attempt
- wrong password
- successful session establishment
- client disconnect

## Files

- `vnc_watch.py`: main watcher
- `run.sh`: start watcher with `sudo journalctl` and desktop notifications
- `launch-monitor.sh`: open terminal and start monitoring interactively
- `launch-log.sh`: open terminal and show readable history
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

```bash
cd /root/projects/vnc-watch
python3 vnc_watch.py --notify
```

If the current user cannot read the journal for `x11vnc`, run it with `sudo`
or add the user to a group with journal access.

On systems where only `sudo journalctl` can read `x11vnc` logs, use this
instead so notifications still appear in your own desktop session:

```bash
cd /root/projects/vnc-watch
sudo journalctl -u x11vnc -f -n 0 --no-pager --output short-iso | python3 vnc_watch.py --notify --stdin
```

Or just run:

```bash
cd /root/projects/vnc-watch
./run.sh
```

`run.sh` asks for the sudo password once, then starts monitoring in the tray and
returns control to the desktop.

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
