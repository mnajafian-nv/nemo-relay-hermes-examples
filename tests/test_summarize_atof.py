from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "scripts"
EXAMPLES = Path(__file__).parents[1] / "examples"
sys.path.insert(0, str(SCRIPTS))

import summarize_atof


class SummarizeAtofTests(unittest.TestCase):
    def test_example_trace_summarizes_the_terminal_task(self) -> None:
        summary = summarize_atof.summarize(
            summarize_atof.load_events(EXAMPLES / "terminal-task.atof.jsonl")
        )

        self.assertEqual(
            summary,
            {
                "events": 4,
                "completed_llm_scopes": 1,
                "tool_calls": 1,
                "tool_errors": 0,
                "correlated_events": 4,
            },
        )

    def test_summarize_counts_completed_scopes_and_tools(self) -> None:
        events = [
            {"kind": "scope", "category": "llm", "scope_category": "end", "uuid": "llm"},
            {"kind": "scope", "category": "tool", "scope_category": "start", "uuid": "tool"},
            {
                "kind": "scope",
                "category": "tool",
                "scope_category": "end",
                "uuid": "tool",
                "metadata": {"otel.status_code": "ERROR"},
            },
        ]

        self.assertEqual(
            summarize_atof.summarize(events),
            {
                "events": 3,
                "completed_llm_scopes": 1,
                "tool_calls": 1,
                "tool_errors": 1,
                "correlated_events": 3,
            },
        )

    def test_validate_trace_requirements_rejects_missing_llm_scope(self) -> None:
        with self.assertRaisesRegex(ValueError, "completed LLM scope"):
            summarize_atof.validate_trace_requirements(
                [],
                {
                    "completed_llm_scopes": 0,
                    "tool_calls": 1,
                    "tool_errors": 0,
                },
                require_llm=True,
                require_tool=True,
                require_no_tool_errors=True,
                required_tool_command=None,
                required_tool_names=[],
            )

    def test_validate_trace_accepts_required_tool_command(self) -> None:
        events = summarize_atof.load_events(EXAMPLES / "terminal-task.atof.jsonl")

        summarize_atof.validate_trace_requirements(
            events,
            summarize_atof.summarize(events),
            require_llm=True,
            require_tool=True,
            require_no_tool_errors=True,
            required_tool_command="sample.py",
            required_tool_names=[],
        )

    def test_validate_trace_requirements_rejects_missing_tool_call(self) -> None:
        with self.assertRaisesRegex(ValueError, "tool call"):
            summarize_atof.validate_trace_requirements(
                [],
                {
                    "completed_llm_scopes": 1,
                    "tool_calls": 0,
                    "tool_errors": 0,
                },
                require_llm=True,
                require_tool=True,
                require_no_tool_errors=True,
                required_tool_command=None,
                required_tool_names=[],
            )

    def test_validate_trace_requirements_rejects_tool_errors(self) -> None:
        with self.assertRaisesRegex(ValueError, "error-free tool calls"):
            summarize_atof.validate_trace_requirements(
                [],
                {
                    "completed_llm_scopes": 1,
                    "tool_calls": 1,
                    "tool_errors": 1,
                },
                require_llm=True,
                require_tool=True,
                require_no_tool_errors=True,
                required_tool_command=None,
                required_tool_names=[],
            )

    def test_validate_trace_rejects_missing_required_tool_command(self) -> None:
        events = [
            {
                "kind": "scope",
                "category": "tool",
                "scope_category": "start",
                "data": {"command": "python3 another_file.py"},
            }
        ]

        with self.assertRaisesRegex(ValueError, "sample.py"):
            summarize_atof.validate_trace_requirements(
                events,
                {
                    "completed_llm_scopes": 1,
                    "tool_calls": 1,
                    "tool_errors": 0,
                },
                require_llm=True,
                require_tool=True,
                require_no_tool_errors=True,
                required_tool_command="sample.py",
                required_tool_names=[],
            )

    def test_validate_trace_accepts_required_tool_name(self) -> None:
        events = [
            {
                "kind": "scope",
                "category": "tool",
                "scope_category": "start",
                "uuid": "web-search",
                "name": "web_search",
            },
            {
                "kind": "scope",
                "category": "tool",
                "scope_category": "end",
                "uuid": "web-search",
                "metadata": {"otel.status_code": "OK"},
            },
        ]

        summarize_atof.validate_trace_requirements(
            events,
            {
                "completed_llm_scopes": 1,
                "tool_calls": 1,
                "tool_errors": 0,
            },
            require_llm=True,
            require_tool=True,
            require_no_tool_errors=True,
            required_tool_command=None,
            required_tool_names=["web_search"],
        )

    def test_validate_trace_rejects_missing_required_tool_name(self) -> None:
        events = [
            {
                "kind": "scope",
                "category": "tool",
                "scope_category": "start",
                "uuid": "terminal",
                "name": "terminal",
            },
            {
                "kind": "scope",
                "category": "tool",
                "scope_category": "end",
                "uuid": "terminal",
                "metadata": {"otel.status_code": "OK"},
            },
        ]

        with self.assertRaisesRegex(ValueError, "web_search"):
            summarize_atof.validate_trace_requirements(
                events,
                {
                    "completed_llm_scopes": 1,
                    "tool_calls": 1,
                    "tool_errors": 0,
                },
                require_llm=True,
                require_tool=True,
                require_no_tool_errors=True,
                required_tool_command=None,
                required_tool_names=["web_search"],
            )

    def test_validate_trace_accepts_multiple_required_tool_names(self) -> None:
        events = []
        for name in ("read_file", "web_search", "write_file"):
            events.extend(
                [
                    {
                        "kind": "scope",
                        "category": "tool",
                        "scope_category": "start",
                        "uuid": name,
                        "name": name,
                    },
                    {
                        "kind": "scope",
                        "category": "tool",
                        "scope_category": "end",
                        "uuid": name,
                        "metadata": {"otel.status_code": "OK"},
                    },
                ]
            )

        summarize_atof.validate_trace_requirements(
            events,
            {
                "completed_llm_scopes": 1,
                "tool_calls": 3,
                "tool_errors": 0,
            },
            require_llm=True,
            require_tool=True,
            require_no_tool_errors=True,
            required_tool_command=None,
            required_tool_names=["read_file", "web_search", "write_file"],
        )

    def test_validate_trace_rejects_required_tool_without_matching_end(self) -> None:
        events = [
            {
                "kind": "scope",
                "category": "tool",
                "scope_category": "start",
                "uuid": "web-search",
                "name": "web_search",
            }
        ]

        with self.assertRaisesRegex(ValueError, "successful tool named 'web_search'"):
            summarize_atof.validate_trace_requirements(
                events,
                {
                    "completed_llm_scopes": 1,
                    "tool_calls": 1,
                    "tool_errors": 0,
                },
                require_llm=True,
                require_tool=True,
                require_no_tool_errors=True,
                required_tool_command=None,
                required_tool_names=["web_search"],
            )
