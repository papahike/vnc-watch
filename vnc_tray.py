#!/usr/bin/env python3
"""Tray UI for VNC watch."""

from __future__ import annotations

import argparse
import fcntl
import signal
import sys
import threading
from pathlib import Path

import gi

gi.require_version("Gtk", "3.0")
gi.require_version("Notify", "0.7")

from gi.repository import GLib, Gtk, Notify  # noqa: E402

try:
    gi.require_version("AppIndicator3", "0.1")
    from gi.repository import AppIndicator3  # type: ignore[attr-defined]  # noqa: E402
except (ImportError, ValueError):
    AppIndicator3 = None  # type: ignore[assignment,misc]

from watchlib import Event, append_event, format_event_line, kind_label, kind_summary, load_events, parse_event


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Tray watcher for x11vnc events")
    parser.add_argument(
        "--history-file",
        default=str(Path(__file__).resolve().parent / "logs" / "events.jsonl"),
        help="path to JSONL history file",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="read lines from stdin",
    )
    parser.add_argument(
        "--lock-file",
        default=str(Path(__file__).resolve().parent / "logs" / "tray.lock"),
        help="lock file to prevent duplicate tray instances",
    )
    return parser.parse_args()


class TrayApp:
    def __init__(self, history_file: Path, lock_file: Path) -> None:
        self.history_file = history_file
        self.input_stream_closed = False
        history_file.parent.mkdir(parents=True, exist_ok=True)
        self.recent_events: list[Event] = []
        self.lock_handle = lock_file.open("w", encoding="utf-8")
        fcntl.flock(self.lock_handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        self.load_recent_history()

        Notify.init("vnc-watch")

        self.menu = self.build_menu()
        self.status_icon: Gtk.StatusIcon | None = None
        self.indicator = None

        if AppIndicator3 is not None:
            self.indicator = AppIndicator3.Indicator.new(
                "vnc-watch",
                "network-idle",
                AppIndicator3.IndicatorCategory.SYSTEM_SERVICES,
            )
            self.indicator.set_title("VNC Watch: мониторинг активен")
            self.indicator.set_menu(self.menu)
            self.indicator.set_status(AppIndicator3.IndicatorStatus.ACTIVE)
        else:
            self.status_icon = Gtk.StatusIcon.new_from_icon_name("network-idle")
            self.status_icon.set_title("VNC Watch")
            self.status_icon.set_tooltip_text("VNC Watch: мониторинг активен")
            self.status_icon.set_visible(True)
            self.status_icon.connect("popup-menu", self.on_popup_menu)
            self.status_icon.connect("activate", self.on_activate)

    def load_recent_history(self) -> None:
        for payload in load_events(self.history_file)[-20:]:
            self.recent_events.append(
                Event(
                    kind=str(payload.get("kind", "")),
                    ip=payload.get("ip"),
                    raw_line=str(payload.get("raw_line", "")),
                    timestamp=payload.get("timestamp"),
                )
            )

    def build_menu(self) -> Gtk.Menu:
        menu = Gtk.Menu()

        title = Gtk.MenuItem(label="VNC Watch")
        title.set_sensitive(False)
        menu.append(title)

        show_item = Gtk.MenuItem(label="Показать последние события")
        show_item.connect("activate", self.show_recent_events)
        menu.append(show_item)

        quit_item = Gtk.MenuItem(label="Выход")
        quit_item.connect("activate", self.quit_app)
        menu.append(quit_item)

        menu.show_all()
        return menu

    def on_popup_menu(self, _icon: Gtk.StatusIcon, button: int, activate_time: int) -> None:
        self.menu.popup(None, None, Gtk.StatusIcon.position_menu, self.status_icon, button, activate_time)

    def on_activate(self, _icon: Gtk.StatusIcon) -> None:
        self.show_recent_events(None)

    def show_recent_events(self, _item: Gtk.MenuItem | None) -> None:
        if self.recent_events:
            lines = [self.render_event(event) for event in self.recent_events[-12:]]
            text = "\n".join(lines)
        else:
            text = "Событий пока нет."

        dialog = Gtk.MessageDialog(
            message_type=Gtk.MessageType.INFO,
            buttons=Gtk.ButtonsType.OK,
            text="Последние события VNC",
        )
        dialog.format_secondary_text(text)
        dialog.run()
        dialog.destroy()

    def render_event(self, event: Event) -> str:
        payload = {
            "kind": event.kind,
            "ip": event.ip,
            "raw_line": event.raw_line,
            "timestamp": event.timestamp,
        }
        return format_event_line(payload)

    def handle_event(self, event: Event) -> None:
        self.recent_events.append(event)
        self.recent_events = self.recent_events[-50:]
        append_event(self.history_file, event)
        status_text = f"{kind_label(event.kind)}: {event.ip or '-'}"
        if self.indicator is not None:
            self.indicator.set_title(status_text)
        elif self.status_icon is not None:
            self.status_icon.set_tooltip_text(status_text)

        notification = Notify.Notification.new(
            notification_title(event.kind),
            kind_summary(event.kind, event.ip),
            None,
        )
        notification.set_timeout(Notify.EXPIRES_NEVER)
        notification.set_urgency(notification_urgency(event.kind))
        notification.show()

    def quit_app(self, _item: Gtk.MenuItem | None) -> None:
        Gtk.main_quit()

    def handle_input_closed(self) -> bool:
        """Close the tray if its journal reader disappeared unexpectedly."""
        self.input_stream_closed = True
        Gtk.main_quit()
        return GLib.SOURCE_REMOVE


def stdin_worker(app: TrayApp) -> None:
    for line in sys.stdin:
        event = parse_event(line.rstrip("\n"))
        if event:
            GLib.idle_add(app.handle_event, event)
    GLib.idle_add(app.handle_input_closed)


def notification_urgency(kind: str) -> Notify.Urgency:
    if kind in {"auth_failed", "session_established"}:
        return Notify.Urgency.CRITICAL
    if kind == "connect_attempt":
        return Notify.Urgency.NORMAL
    return Notify.Urgency.LOW


def notification_title(kind: str) -> str:
    titles = {
        "connect_attempt": "VNC: входящее соединение",
        "auth_failed": "VNC: ошибка аутентификации",
        "session_established": "VNC: подключение установлено",
        "client_gone": "VNC: подключение завершено",
    }
    return titles.get(kind, "VNC: событие")


def main() -> int:
    args = parse_args()
    history_file = Path(args.history_file)
    lock_file = Path(args.lock_file)

    try:
        app = TrayApp(history_file, lock_file)
    except BlockingIOError:
        print("VNC Watch is already running in tray.")
        return 0

    signal.signal(signal.SIGINT, lambda *_args: Gtk.main_quit())
    signal.signal(signal.SIGTERM, lambda *_args: Gtk.main_quit())

    if args.stdin:
        thread = threading.Thread(target=stdin_worker, args=(app,), daemon=True)
        thread.start()

    Gtk.main()
    return 75 if app.input_stream_closed else 0


if __name__ == "__main__":
    raise SystemExit(main())
