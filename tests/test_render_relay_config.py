from __future__ import annotations

import sys
import tempfile
import unittest
from contextlib import redirect_stderr
from io import StringIO
from pathlib import Path

SCRIPTS = Path(__file__).parents[1] / "scripts"
REPOSITORY_ROOT = Path(__file__).parents[1]
sys.path.insert(0, str(SCRIPTS))

import render_relay_config


class RenderRelayConfigTests(unittest.TestCase):
    def test_smoke_contract_defines_task_prompt_and_expected_output(self) -> None:
        values: dict[str, str] = {}
        for line in (REPOSITORY_ROOT / "config" / "smoke.env").read_text(
            encoding="utf-8"
        ).splitlines():
            if "=" not in line or line.lstrip().startswith("#"):
                continue
            key, value = line.split("=", maxsplit=1)
            values[key] = value.strip().strip("'\"")

        self.assertTrue(values["SMOKE_QUERY"])
        self.assertTrue(values["SMOKE_EXPECTED_OUTPUT"])

    def test_render_config_uses_absolute_output_paths(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            config = render_relay_config.render_config(
                Path(directory) / "trace output", "nvidia/test-model"
            )

        self.assertIn('model_name = "nvidia/test-model"', config)
        self.assertIn('filename = "run.jsonl"', config)
        self.assertNotIn("__RELAY_OUTPUT_ROOT__", config)

    def test_main_rejects_empty_model_name(self) -> None:
        with tempfile.TemporaryDirectory() as directory:
            with redirect_stderr(StringIO()), self.assertRaises(SystemExit):
                render_relay_config.main(
                    [
                        "--output",
                        str(Path(directory) / "plugins.toml"),
                        "--output-directory",
                        directory,
                        "--model-name",
                        "   ",
                    ]
                )
