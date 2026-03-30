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
    line = "2026-03-30T12:09:36+0500 host x11vnc[1385]: Got connection from client 11.0.0.21"
    assert extract_timestamp(line) == "2026-03-30T12:09:36+0500"


def test_parse_event_detects_session_established() -> None:
    line = (
        "2026-03-30T12:09:57+0500 AG-231-1.yg.loc x11vnc[1385]: "
        "30/03/2026 12:09:57 client_set_net: 11.0.0.21  0.0019"
    )
    event = parse_event(line)
    assert event == Event(
        kind="session_established",
        ip="11.0.0.21",
        raw_line=line,
        timestamp="2026-03-30T12:09:57+0500",
    )


def test_parse_event_ignores_unrelated_lines() -> None:
    assert parse_event("selection_send: no send: uninitialized clients") is None


def test_append_and_load_events_roundtrip(tmp_path) -> None:
    history = tmp_path / "events.jsonl"
    event = Event(
        kind="client_gone",
        ip="10.12.4.252",
        raw_line="2026-03-30T11:40:24+0500 Client 10.12.4.252 gone",
        timestamp="2026-03-30T11:40:24+0500",
    )

    append_event(history, event)

    loaded = load_events(history)
    assert loaded == [
        {
            "kind": "client_gone",
            "ip": "10.12.4.252",
            "raw_line": "2026-03-30T11:40:24+0500 Client 10.12.4.252 gone",
            "timestamp": "2026-03-30T11:40:24+0500",
        }
    ]


def test_load_events_skips_invalid_json_and_backfills_timestamp(tmp_path) -> None:
    history = tmp_path / "events.jsonl"
    payload = {
        "kind": "connect_attempt",
        "ip": "11.0.0.21",
        "raw_line": "2026-03-30T12:07:35+0500 AG-231-1 Got connection from client 11.0.0.21",
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
    assert "11.0.0.21" in kind_summary("session_established", "11.0.0.21")
    assert pretty_timestamp("2026-03-30T12:09:57+0500") == "30.03.2026 12:09:57"


def test_format_event_line_is_human_readable() -> None:
    payload = {
        "kind": "session_established",
        "ip": "11.0.0.21",
        "raw_line": "ignored",
        "timestamp": "2026-03-30T12:09:57+0500",
    }

    line = format_event_line(payload)

    assert "30.03.2026 12:09:57" in line
    assert "Подключение установлено" in line
    assert "11.0.0.21" in line
