from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import summarize_atof


class SummarizeAtofTests(unittest.TestCase):
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
