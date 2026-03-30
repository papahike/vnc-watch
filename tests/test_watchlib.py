from __future__ import annotations

import json

from watchlib import (
    Event,
    append_event,
    extract_timestamp,
    format_event_line,
    kind_label,
    kind_summary,
    load_events,
    parse_event,
    pretty_timestamp,
)


def test_extract_timestamp_returns_iso_prefix() -> None:
    line = "2026-03-30T12:09:36+0500 host.example x11vnc[1385]: Got connection from client 203.0.113.21"
    assert extract_timestamp(line) == "2026-03-30T12:09:36+0500"


def test_parse_event_detects_session_established() -> None:
    line = (
        "2026-03-30T12:09:57+0500 host.example x11vnc[1385]: "
        "30/03/2026 12:09:57 client_set_net: 203.0.113.21  0.0019"
    )
    event = parse_event(line)
    assert event == Event(
        kind="session_established",
        ip="203.0.113.21",
        raw_line=line,
        timestamp="2026-03-30T12:09:57+0500",
    )


def test_parse_event_ignores_unrelated_lines() -> None:
    assert parse_event("selection_send: no send: uninitialized clients") is None


def test_append_and_load_events_roundtrip(tmp_path) -> None:
    history = tmp_path / "events.jsonl"
    event = Event(
        kind="client_gone",
        ip="198.51.100.25",
        raw_line="2026-03-30T11:40:24+0500 Client 198.51.100.25 gone",
        timestamp="2026-03-30T11:40:24+0500",
    )

    append_event(history, event)

    loaded = load_events(history)
    assert loaded == [
        {
            "kind": "client_gone",
            "ip": "198.51.100.25",
            "raw_line": "2026-03-30T11:40:24+0500 Client 198.51.100.25 gone",
            "timestamp": "2026-03-30T11:40:24+0500",
        }
    ]


def test_load_events_skips_invalid_json_and_backfills_timestamp(tmp_path) -> None:
    history = tmp_path / "events.jsonl"
    payload = {
        "kind": "connect_attempt",
        "ip": "203.0.113.21",
        "raw_line": "2026-03-30T12:07:35+0500 host.example Got connection from client 203.0.113.21",
        "timestamp": None,
    }
    history.write_text(
        "{not-json}\n" + json.dumps(payload, ensure_ascii=True) + "\n",
        encoding="utf-8",
    )

    loaded = load_events(history)

    assert len(loaded) == 1
    assert loaded[0]["timestamp"] == "2026-03-30T12:07:35+0500"


def test_label_summary_and_pretty_formatting() -> None:
    assert kind_label("auth_failed") == "Неверный пароль"
    assert "203.0.113.21" in kind_summary("session_established", "203.0.113.21")
    assert pretty_timestamp("2026-03-30T12:09:57+0500") == "30.03.2026 12:09:57"


def test_format_event_line_is_human_readable() -> None:
    payload = {
        "kind": "session_established",
        "ip": "203.0.113.21",
        "raw_line": "ignored",
        "timestamp": "2026-03-30T12:09:57+0500",
    }

    line = format_event_line(payload)

    assert "30.03.2026 12:09:57" in line
    assert "Подключение установлено" in line
    assert "203.0.113.21" in line
