from __future__ import annotations

from argparse import Namespace

import show_log
from watchlib import Event, append_event


def test_show_log_reports_empty_history(tmp_path, monkeypatch, capsys) -> None:
    history = tmp_path / "events.jsonl"
    monkeypatch.setattr(
        show_log,
        "parse_args",
        lambda: Namespace(history_file=str(history), limit=30),
    )

    result = show_log.main()
    captured = capsys.readouterr()

    assert result == 0
    assert "Лог пока пуст" in captured.out


def test_show_log_prints_recent_readable_events(tmp_path, monkeypatch, capsys) -> None:
    history = tmp_path / "events.jsonl"
    append_event(
        history,
        Event(
            kind="connect_attempt",
            ip="10.12.4.252",
            raw_line="2026-03-30T11:35:48+0500 Got connection from client 10.12.4.252",
            timestamp="2026-03-30T11:35:48+0500",
        ),
    )
    append_event(
        history,
        Event(
            kind="session_established",
            ip="10.12.4.252",
            raw_line="2026-03-30T11:35:57+0500 client_set_net: 10.12.4.252 0.0189",
            timestamp="2026-03-30T11:35:57+0500",
        ),
    )
    monkeypatch.setattr(
        show_log,
        "parse_args",
        lambda: Namespace(history_file=str(history), limit=1),
    )

    result = show_log.main()
    captured = capsys.readouterr()

    assert result == 0
    assert "Последние события VNC" in captured.out
    assert "Подключение установлено" in captured.out
    assert "10.12.4.252" in captured.out
    assert "Всего событий в истории: 2" in captured.out
