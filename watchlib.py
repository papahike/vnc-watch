#!/usr/bin/env python3
"""Shared helpers for VNC watch tools."""

from __future__ import annotations

import json
import re
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


EVENT_PATTERNS = (
    ("connect_attempt", re.compile(r"Got connection from client (\S+)")),
    ("auth_failed", re.compile(r"authentication failed from (\S+)")),
    ("password_failed", re.compile(r"password check failed")),
    ("session_established", re.compile(r"client_set_net: (\S+)")),
    ("client_gone", re.compile(r"Client (\S+) gone")),
)

ISO_PREFIX_RE = re.compile(r"^(\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}[+-]\d{4})")


@dataclass
class Event:
    kind: str
    ip: str | None
    raw_line: str
    timestamp: str | None


def extract_timestamp(line: str) -> str | None:
    match = ISO_PREFIX_RE.search(line)
    return match.group(1) if match else None


def parse_event(line: str) -> Event | None:
    for kind, pattern in EVENT_PATTERNS:
        match = pattern.search(line)
        if match:
            ip = match.group(1) if match.lastindex else None
            return Event(
                kind=kind,
                ip=ip,
                raw_line=line,
                timestamp=extract_timestamp(line),
            )
    return None


def append_event(history_path: Path, event: Event) -> None:
    history_path.parent.mkdir(parents=True, exist_ok=True)
    with history_path.open("a", encoding="utf-8") as handle:
        handle.write(json.dumps(asdict(event), ensure_ascii=True) + "\n")


def load_events(history_path: Path) -> list[dict[str, str | None]]:
    if not history_path.exists():
        return []

    events: list[dict[str, str | None]] = []
    with history_path.open("r", encoding="utf-8") as handle:
        for line in handle:
            line = line.strip()
            if not line:
                continue
            try:
                payload = json.loads(line)
            except json.JSONDecodeError:
                continue
            if not payload.get("timestamp"):
                payload["timestamp"] = extract_timestamp(payload.get("raw_line", ""))
            events.append(payload)
    return events


def kind_label(kind: str) -> str:
    labels = {
        "connect_attempt": "Попытка подключения",
        "auth_failed": "Неверный пароль",
        "password_failed": "Ошибка проверки пароля",
        "session_established": "Подключение установлено",
        "client_gone": "Клиент отключился",
    }
    return labels.get(kind, kind)


def kind_summary(kind: str, ip: str | None) -> str:
    ip_text = ip or "неизвестный IP"
    summaries = {
        "connect_attempt": f"Зафиксировано входящее VNC-соединение от {ip_text}",
        "auth_failed": f"Отклонена аутентификация VNC от {ip_text}",
        "password_failed": "Сервер отклонил пароль клиента VNC",
        "session_established": f"Установлено VNC-подключение от {ip_text}",
        "client_gone": f"Завершено VNC-подключение от {ip_text}",
    }
    return summaries.get(kind, f"Событие VNC: {ip_text}")


def pretty_timestamp(timestamp: str | None) -> str:
    if not timestamp:
        return "без времени"
    try:
        parsed = datetime.strptime(timestamp, "%Y-%m-%dT%H:%M:%S%z")
    except ValueError:
        return timestamp
    return parsed.strftime("%d.%m.%Y %H:%M:%S")


def format_event_line(payload: dict[str, str | None]) -> str:
    timestamp = pretty_timestamp(payload.get("timestamp"))
    label = kind_label(str(payload.get("kind", "")))
    ip = payload.get("ip") or "-"
    summary = kind_summary(str(payload.get("kind", "")), payload.get("ip"))
    return f"{timestamp} | {label:24} | {ip:15} | {summary}"
