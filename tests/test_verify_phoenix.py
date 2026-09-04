from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import verify_phoenix


class VerifyPhoenixTests(unittest.TestCase):
    def test_project_trace_count_returns_matching_trace_count(self) -> None:
        payload = {
            "data": {
                "projects": {
                    "edges": [
                        {"node": {"name": "other", "traceCount": 3}},
                        {"node": {"name": "tutorial", "traceCount": 1}},
                    ]
                }
            }
        }

        self.assertEqual(verify_phoenix.project_trace_count(payload, "tutorial"), 1)

    def test_project_trace_count_returns_zero_for_missing_project(self) -> None:
        payload = {"data": {"projects": {"edges": []}}}

        self.assertEqual(verify_phoenix.project_trace_count(payload, "tutorial"), 0)

    def test_project_trace_count_rejects_invalid_response(self) -> None:
        with self.assertRaisesRegex(ValueError, "unexpected project response"):
            verify_phoenix.project_trace_count({}, "tutorial")

    def test_project_cost_summary_returns_matching_totals(self) -> None:
        payload = {
            "data": {
                "projects": {
                    "edges": [
                        {
                            "node": {
                                "name": "tutorial",
                                "costSummary": {
                                    "total": {"cost": 0.0125, "tokens": 2048.0}
                                },
                            }
                        }
                    ]
                }
            }
        }

        self.assertEqual(
            verify_phoenix.project_cost_summary(payload, "tutorial"),
            (0.0125, 2048.0),
        )

    def test_project_cost_summary_returns_none_while_summary_is_unavailable(
        self,
    ) -> None:
        payload = {
            "data": {
                "projects": {
                    "edges": [
                        {"node": {"name": "tutorial", "costSummary": None}}
                    ]
                }
            }
        }

        self.assertIsNone(
            verify_phoenix.project_cost_summary(payload, "tutorial")
        )

    def test_project_cost_summary_rejects_invalid_totals(self) -> None:
        payload = {
            "data": {
                "projects": {
                    "edges": [
                        {
                            "node": {
                                "name": "tutorial",
                                "costSummary": {
                                    "total": {"cost": -1, "tokens": 2048}
                                },
                            }
                        }
                    ]
                }
            }
        }

        with self.assertRaisesRegex(ValueError, "invalid cost total"):
            verify_phoenix.project_cost_summary(payload, "tutorial")

    def test_trace_span_names_returns_unique_names(self) -> None:
        payload = {
            "data": [
                {
                    "spans": [
                        {"name": "hermes.session"},
                        {"name": "web_search"},
                        {"name": "web_search"},
                    ]
                }
            ]
        }

        self.assertEqual(
            verify_phoenix.trace_span_names(payload),
            {"hermes.session", "web_search"},
        )

    def test_trace_span_names_rejects_invalid_span_list(self) -> None:
        with self.assertRaisesRegex(ValueError, "invalid span list"):
            verify_phoenix.trace_span_names({"data": [{"spans": None}]})
