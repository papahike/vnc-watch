#!/usr/bin/env python3
"""Watch x11vnc journal events and emit simple alerts."""

from __future__ import annotations

import argparse
import os
import shutil
import signal
import subprocess
import sys
from pathlib import Path
from typing import Iterable

from watchlib import Event, append_event, kind_summary, parse_event


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Monitor x11vnc logs and write normalized events."
    )
    parser.add_argument(
        "--unit",
        default="x11vnc",
        help="systemd unit name to follow with journalctl",
    )
    parser.add_argument(
        "--history-file",
        default=str(Path(__file__).resolve().parent / "logs" / "events.jsonl"),
        help="path to JSONL history file",
    )
    parser.add_argument(
        "--notify",
        action="store_true",
        help="show desktop notifications via notify-send when available",
    )
    parser.add_argument(
        "--once",
        action="store_true",
        help="read existing journal entries and exit without following",
    )
    parser.add_argument(
        "--stdin",
        action="store_true",
        help="read journal lines from stdin instead of launching journalctl",
    )
    return parser.parse_args()


def build_journalctl_command(unit: str, once: bool) -> list[str]:
    cmd = [
        "journalctl",
        "-u",
        unit,
        "--no-pager",
        "--output",
        "short-iso",
    ]
    if once:
        cmd.extend(["-n", "200"])
    else:
        cmd.extend(["-f", "-n", "0"])
    return cmd


def iter_journal_lines(cmd: list[str]) -> Iterable[str]:
    proc = subprocess.Popen(
        cmd,
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
        text=True,
        bufsize=1,
    )

    def _shutdown(_signum: int, _frame: object) -> None:
        proc.terminate()

    signal.signal(signal.SIGINT, _shutdown)
    signal.signal(signal.SIGTERM, _shutdown)

    assert proc.stdout is not None
    for line in proc.stdout:
        yield line.rstrip("\n")

    return_code = proc.wait()
    if return_code not in (0, -15):
        raise RuntimeError(f"journalctl exited with code {return_code}")


def iter_stdin_lines() -> Iterable[str]:
    for line in sys.stdin:
        yield line.rstrip("\n")


def maybe_notify(event: Event) -> None:
    notify_send = shutil.which("notify-send")
    if not notify_send:
        return

    title, body = format_notification(event)
    urgency = notification_urgency(event.kind)
    subprocess.run(
        [notify_send, "-u", urgency, "-t", "0", title, body],
        check=False,
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
        env=os.environ.copy(),
    )


def format_notification(event: Event) -> tuple[str, str]:
    if event.kind == "connect_attempt":
        return ("VNC: входящее соединение", kind_summary(event.kind, event.ip))
    if event.kind == "auth_failed":
        return ("VNC: ошибка аутентификации", kind_summary(event.kind, event.ip))
    if event.kind == "session_established":
        return ("VNC: подключение установлено", kind_summary(event.kind, event.ip))
    if event.kind == "client_gone":
        return ("VNC: подключение завершено", kind_summary(event.kind, event.ip))
    return ("VNC: событие", event.raw_line)


def notification_urgency(kind: str) -> str:
    if kind in {"auth_failed", "session_established"}:
        return "critical"
    if kind == "connect_attempt":
        return "normal"
    return "low"


def main() -> int:
    args = parse_args()
    history_path = Path(args.history_file)

    try:
        if args.stdin:
            line_source = iter_stdin_lines()
        else:
            cmd = build_journalctl_command(args.unit, args.once)
            line_source = iter_journal_lines(cmd)

        for line in line_source:
            event = parse_event(line)
            if not event:
                continue
            append_event(history_path, event)
            print(f"[{event.kind}] {event.ip or '-'} | {event.raw_line}")
            if args.notify:
                maybe_notify(event)
    except RuntimeError as exc:
        print(str(exc), file=sys.stderr)
        return 1

    return 0


if __name__ == "__main__":
    raise SystemExit(main())
