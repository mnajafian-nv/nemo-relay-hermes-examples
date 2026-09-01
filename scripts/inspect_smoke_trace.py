#!/usr/bin/env python3
"""Print the scope-level timeline from a NeMo Relay ATOF trace."""

from __future__ import annotations

import argparse
import json
from collections import Counter
from pathlib import Path
from typing import Any


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Print the scope-level timeline from a Relay ATOF JSONL file."
    )
    parser.add_argument("trace", type=Path, help="Path to an ATOF JSONL trace")
    return parser.parse_args()


def read_events(trace_path: Path) -> list[dict[str, Any]]:
    events: list[dict[str, Any]] = []
    with trace_path.open(encoding="utf-8") as trace_file:
        for line_number, line in enumerate(trace_file, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                message = f"{trace_path}:{line_number}: invalid JSON: {error.msg}"
                raise SystemExit(message) from error
            if not isinstance(event, dict):
                message = f"{trace_path}:{line_number}: expected a JSON object"
                raise SystemExit(message)
            events.append(event)
    return events


def format_scope_event(event: dict[str, Any]) -> str:
    timestamp = event.get("timestamp", "unknown time")
    state = event.get("scope_category", "unknown state")
    name = event.get("name", "unnamed scope")
    return f"{timestamp}  {state:5}  {name}"


def main() -> None:
    args = parse_args()
    if not args.trace.is_file():
        raise SystemExit(f"Trace does not exist or is not a file: {args.trace}")

    events = read_events(args.trace)
    scopes = [event for event in events if event.get("kind") == "scope"]
    event_counts = Counter(event.get("name", "unnamed event") for event in events)

    print(f"Trace: {args.trace}")
    print(f"Events: {len(events)}")
    print(f"Scope events: {len(scopes)}")
    print("\nScope timeline:")
    for event in scopes:
        print(format_scope_event(event))

    print("\nMost frequent events:")
    for name, count in event_counts.most_common(5):
        print(f"{count:4}  {name}")


if __name__ == "__main__":
    main()
