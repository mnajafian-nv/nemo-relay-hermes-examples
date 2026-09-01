#!/usr/bin/env python3
"""Render the Relay observability configuration used by this tutorial."""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path


def toml_string(value: str) -> str:
    return json.dumps(value, ensure_ascii=False)


def render_config(output_directory: Path, model_name: str) -> str:
    root = output_directory.expanduser().resolve()
    return f'''version = 1

[[components]]
kind = "observability"
enabled = true

[components.config]
version = 3
enable_full_payloads = false

[components.config.atof]
enabled = true

[[components.config.atof.sinks]]
type = "file"
output_directory = {toml_string(str(root / "atof"))}
filename = "run.jsonl"
mode = "overwrite"

[components.config.atif]
enabled = true
agent_name = "Hermes Agent"
model_name = {toml_string(model_name)}
output_directory = {toml_string(str(root / "atif"))}
filename_template = "trajectory-{{session_id}}.json"
'''


def parse_args(argv: list[str]) -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Render plugins.toml for the Hermes + NeMo Relay tutorial."
    )
    parser.add_argument("--output", required=True, type=Path)
    parser.add_argument("--output-directory", required=True, type=Path)
    parser.add_argument("--model-name", required=True)
    args = parser.parse_args(argv)
    if not args.model_name.strip():
        parser.error("--model-name cannot be empty")
    return args


def main(argv: list[str] | None = None) -> int:
    args = parse_args(sys.argv[1:] if argv is None else argv)
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(
        render_config(args.output_directory, args.model_name.strip()), encoding="utf-8"
    )
    print(args.output.resolve())
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
