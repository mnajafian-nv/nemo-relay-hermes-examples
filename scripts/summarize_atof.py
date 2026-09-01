#!/usr/bin/env python3
"""Validate and summarize a NeMo Relay ATOF JSONL event stream."""

from __future__ import annotations

import argparse
import collections
import json
import sys
from pathlib import Path
from typing import Any

Event = dict[str, Any]


def load_events(path: Path) -> list[Event]:
    events: list[Event] = []
    with path.open(encoding="utf-8") as stream:
        for line_number, line in enumerate(stream, start=1):
            if not line.strip():
                continue
            try:
                event = json.loads(line)
            except json.JSONDecodeError as error:
                raise ValueError(f"{path}:{line_number}: invalid JSON: {error.msg}") from error
            if not isinstance(event, dict):
                raise TypeError(f"{path}:{line_number}: expected a JSON object")
            events.append(event)
    if not events:
        raise ValueError(f"{path}: no ATOF events found")
    return events


def metadata(event: Event) -> dict[str, Any]:
    value = event.get("metadata")
    return value if isinstance(value, dict) else {}


def is_scope(event: Event, category: str, phase: str) -> bool:
    return (
        event.get("kind") == "scope"
        and event.get("category") == category
        and event.get("scope_category") == phase
    )


def is_error_status(event: Event) -> bool:
    status = metadata(event).get("otel.status_code", metadata(event).get("status"))
    return status is not None and str(status).strip().upper() not in {"OK", "SUCCESS", "UNSET"}


def summarize(events: list[Event]) -> dict[str, int]:
    tool_ends = [event for event in events if is_scope(event, "tool", "end")]
    return {
        "events": len(events),
        "completed_llm_scopes": sum(is_scope(event, "llm", "end") for event in events),
        "tool_calls": sum(is_scope(event, "tool", "start") for event in events),
        "tool_errors": sum(is_error_status(event) for event in tool_ends),
        "correlated_events": sum(event.get("uuid") is not None for event in events),
    }


def validate_required_activity(
    summary: dict[str, int], *, require_llm: bool, require_tool: bool
) -> None:
    missing: list[str] = []
    if require_llm and summary["completed_llm_scopes"] == 0:
        missing.append("completed LLM scope")
    if require_tool and summary["tool_calls"] == 0:
        missing.append("tool call")
    if missing:
        raise ValueError(f"trace is missing required activity: {', '.join(missing)}")


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Summarize a Relay ATOF JSONL trace.")
    parser.add_argument("trace", type=Path, help="Path to an ATOF JSONL trace")
    parser.add_argument(
        "--require-completed-llm-scope",
        action="store_true",
        help="Fail when the trace has no completed LLM scope",
    )
    parser.add_argument(
        "--require-tool-call",
        action="store_true",
        help="Fail when the trace has no tool-call scope",
    )
    return parser.parse_args(argv)


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    try:
        summary = summarize(load_events(args.trace))
        validate_required_activity(
            summary,
            require_llm=args.require_completed_llm_scope,
            require_tool=args.require_tool_call,
        )
    except (OSError, TypeError, ValueError) as error:
        print(f"error: {error}", file=sys.stderr)
        return 1

    print(f"trace: {args.trace}")
    for label, value in summary.items():
        print(f"{label.replace('_', ' ')}: {value}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
