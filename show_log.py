#!/usr/bin/env python3
"""Human-readable viewer for VNC watch history."""

from __future__ import annotations

import argparse
from pathlib import Path

from watchlib import format_event_line, load_events


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Show readable VNC history")
    parser.add_argument(
        "--history-file",
        default=str(Path(__file__).resolve().parent / "logs" / "events.jsonl"),
        help="path to JSONL history file",
    )
    parser.add_argument(
        "--limit",
        type=int,
        default=30,
        help="number of last events to show",
    )
    return parser.parse_args()


def main() -> int:
    args = parse_args()
    events = load_events(Path(args.history_file))
    if not events:
        print("Лог пока пуст. Сначала запустите мониторинг и дождитесь события.")
        return 0

    print("Последние события VNC")
    print("-" * 96)
    for payload in events[-args.limit :]:
        print(format_event_line(payload))
    print("-" * 96)
    print(f"Всего событий в истории: {len(events)}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
