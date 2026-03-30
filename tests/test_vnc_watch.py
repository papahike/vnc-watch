from __future__ import annotations

import io
from argparse import Namespace

import vnc_watch


def test_build_journalctl_command_in_follow_mode() -> None:
    assert vnc_watch.build_journalctl_command("x11vnc", once=False) == [
        "journalctl",
        "-u",
        "x11vnc",
        "--no-pager",
        "--output",
        "short-iso",
        "-f",
        "-n",
        "0",
    ]


def test_build_journalctl_command_in_once_mode() -> None:
    assert vnc_watch.build_journalctl_command("x11vnc", once=True) == [
        "journalctl",
        "-u",
        "x11vnc",
        "--no-pager",
        "--output",
        "short-iso",
        "-n",
        "200",
    ]


def test_notification_urgency_maps_expected_levels() -> None:
    assert vnc_watch.notification_urgency("auth_failed") == "critical"
    assert vnc_watch.notification_urgency("session_established") == "critical"
    assert vnc_watch.notification_urgency("connect_attempt") == "normal"
    assert vnc_watch.notification_urgency("client_gone") == "low"


def test_maybe_notify_invokes_notify_send(monkeypatch) -> None:
    event = vnc_watch.Event(
        kind="session_established",
        ip="11.0.0.21",
        raw_line="raw",
        timestamp="2026-03-30T12:09:57+0500",
    )
    calls: list[list[str]] = []

    monkeypatch.setattr(vnc_watch.shutil, "which", lambda name: "/usr/bin/notify-send")

    def fake_run(cmd, check, stdout, stderr, env):  # type: ignore[no-untyped-def]
        calls.append(cmd)
        return None

    monkeypatch.setattr(vnc_watch.subprocess, "run", fake_run)

    vnc_watch.maybe_notify(event)

    assert calls == [[
        "/usr/bin/notify-send",
        "-u",
        "critical",
        "-t",
        "0",
        "VNC: подключение установлено",
        "Установлено VNC-подключение от 11.0.0.21",
    ]]


def test_main_reads_stdin_writes_history_and_prints(tmp_path, monkeypatch, capsys) -> None:
    history = tmp_path / "events.jsonl"
    stdin_text = "\n".join(
        [
            (
                "2026-03-30T12:07:35+0500 host x11vnc[1385]: "
                "30/03/2026 12:07:35 Got connection from client 11.0.0.21"
            ),
            "unrelated line",
            (
                "2026-03-30T12:09:57+0500 host x11vnc[1385]: "
                "30/03/2026 12:09:57 client_set_net: 11.0.0.21  0.0019"
            ),
            "",
        ]
    )
    monkeypatch.setattr(
        vnc_watch,
        "parse_args",
        lambda: Namespace(
            unit="x11vnc",
            history_file=str(history),
            notify=False,
            once=False,
            stdin=True,
        ),
    )
    monkeypatch.setattr(vnc_watch.sys, "stdin", io.StringIO(stdin_text))

    result = vnc_watch.main()
    captured = capsys.readouterr()

    assert result == 0
    assert "[connect_attempt] 11.0.0.21" in captured.out
    assert "[session_established] 11.0.0.21" in captured.out
    lines = history.read_text(encoding="utf-8").strip().splitlines()
    assert len(lines) == 2
