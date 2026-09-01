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
                {
                    "completed_llm_scopes": 0,
                    "tool_calls": 1,
                    "tool_errors": 0,
                },
                require_llm=True,
                require_tool=True,
                require_no_tool_errors=True,
            )

    def test_validate_trace_requirements_rejects_missing_tool_call(self) -> None:
        with self.assertRaisesRegex(ValueError, "tool call"):
            summarize_atof.validate_trace_requirements(
                {
                    "completed_llm_scopes": 1,
                    "tool_calls": 0,
                    "tool_errors": 0,
                },
                require_llm=True,
                require_tool=True,
                require_no_tool_errors=True,
            )

    def test_validate_trace_requirements_rejects_tool_errors(self) -> None:
        with self.assertRaisesRegex(ValueError, "error-free tool calls"):
            summarize_atof.validate_trace_requirements(
                {
                    "completed_llm_scopes": 1,
                    "tool_calls": 1,
                    "tool_errors": 1,
                },
                require_llm=True,
                require_tool=True,
                require_no_tool_errors=True,
            )
