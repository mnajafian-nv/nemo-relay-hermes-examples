from __future__ import annotations

import sys
import unittest
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "scripts"
sys.path.insert(0, str(SCRIPTS))

import summarize_atif


class SummarizeAtifTests(unittest.TestCase):
    def test_summarize_reports_execution_shape_without_payloads(self) -> None:
        trajectory = {
            "agent": {
                "name": "Hermes Agent",
                "model_name": "nvidia/nvidia/nemotron-3.5-lightning",
            },
            "steps": [
                {"message": "secret prompt"},
                {
                    "llm_call_count": 2,
                    "tool_calls": [
                        {"arguments": "sensitive input"},
                        {"arguments": "other input"},
                    ],
                },
                {"llm_call_count": 1, "tool_calls": []},
            ],
        }

        self.assertEqual(
            summarize_atif.summarize(trajectory),
            {
                "agent": "Hermes Agent",
                "model": "nvidia/nvidia/nemotron-3.5-lightning",
                "steps": 3,
                "llm_calls": 3,
                "requested_tool_calls": 2,
            },
        )

    def test_summarize_rejects_invalid_step_call_counts(self) -> None:
        with self.assertRaisesRegex(ValueError, "llm_call_count"):
            summarize_atif.summarize(
                {
                    "agent": {},
                    "steps": [{"llm_call_count": -1}],
                }
            )
