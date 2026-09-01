#!/usr/bin/env python3
"""Compare Hermes revisions on a trace-validated terminal-output recovery case."""

from __future__ import annotations

import argparse
import json
import os
import py_compile
import shutil
import subprocess
import sys
import time
from dataclasses import asdict, dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import Any


MODEL = "nvidia/nvidia/nemotron-3.5-lightning"
TOKEN = "tok_9f31c_middle"
PLUGIN_NAME = "observability/nemo_relay"
NVIDIA_BASE_URL = "https://inference-api.nvidia.com/v1"


@dataclass
class RunResult:
    arm: str
    run_id: str
    exit_code: int
    llm_calls: int
    tool_calls: int
    tool_result_bytes: int
    trace_valid_recovery: bool
    wall_seconds: float


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--baseline", type=Path, required=True)
    parser.add_argument("--candidate", type=Path, required=True)
    parser.add_argument("--python", type=Path, default=Path(sys.executable))
    parser.add_argument("--model", default=MODEL)
    parser.add_argument("--base-url", default=NVIDIA_BASE_URL)
    parser.add_argument("--repetitions", type=int, default=5)
    parser.add_argument("--timeout-seconds", type=int, default=300)
    parser.add_argument(
        "--output-root",
        type=Path,
        default=Path("/tmp/nemo-relay-hermes-examples")
        / f"output-recovery-{datetime.now(UTC).strftime('%Y%m%dT%H%M%SZ')}",
    )
    args = parser.parse_args()
    if args.repetitions < 1:
        parser.error("--repetitions must be positive")
    for path in (args.baseline, args.candidate, args.python):
        if not path.exists():
            parser.error(f"required path does not exist: {path}")
    if not os.environ.get("NVIDIA_API_KEY"):
        parser.error("NVIDIA_API_KEY must be set in the environment")
    return args


def write_task(project: Path) -> Path:
    project.mkdir(parents=True, exist_ok=True)
    source = project / "noisy_build.py"
    script = project / "noisy_build.pyc"
    source.write_text(
        "for i in range(4000):\n"
        "    print(f'[build] step {i} ' + 'x' * 60)\n"
        "    if i == 2000:\n"
        f"        print('UNIQUE_TOKEN={TOKEN}')\n",
        encoding="utf-8",
    )
    py_compile.compile(str(source), cfile=str(script), doraise=True)
    source.unlink()
    return script


def write_relay_config(trace_path: Path, path: Path) -> None:
    path.write_text(
        "\n".join(
            (
                "version = 1",
                "",
                "[[components]]",
                'kind = "observability"',
                "enabled = true",
                "",
                "[components.config]",
                "version = 3",
                "",
                "[components.config.atof]",
                "enabled = true",
                "",
                "[[components.config.atof.sinks]]",
                'type = "file"',
                f"output_directory = {json.dumps(str(trace_path.parent))}",
                f"filename = {json.dumps(trace_path.name)}",
                'mode = "overwrite"',
            )
        ),
        encoding="utf-8",
    )


def enable_relay_plugin(python: Path, baseline: Path, hermes_home: Path) -> None:
    environment = dict(os.environ)
    environment.update({"PYTHONPATH": str(baseline), "HERMES_HOME": str(hermes_home)})
    subprocess.run(
        [str(python), "-m", "hermes_cli.main", "plugins", "enable", PLUGIN_NAME],
        env=environment,
        check=True,
        text=True,
    )


def trace_metrics(trace_path: Path) -> tuple[int, int, int]:
    llm_calls = tool_calls = tool_result_bytes = 0
    for event in read_events(trace_path):
        if event.get("kind") != "scope":
            continue
        if event.get("category") == "llm" and event.get("scope_category") == "end":
            llm_calls += 1
        elif event.get("category") == "tool":
            if event.get("scope_category") == "start":
                tool_calls += 1
            elif event.get("scope_category") == "end":
                data = event.get("data")
                tool_result_bytes += len(
                    data if isinstance(data, str) else json.dumps(data or "")
                )
    return llm_calls, tool_calls, tool_result_bytes


def trace_valid_recovery(response: str, trace_path: Path) -> bool:
    """Verify one execution plus retrieval of the candidate's spill artifact."""
    if TOKEN not in response:
        return False

    script_commands: list[str] = []
    saw_spill_retrieval = False
    for event in read_events(trace_path):
        if not (
            event.get("kind") == "scope"
            and event.get("category") == "tool"
            and event.get("scope_category") == "start"
        ):
            continue

        tool_name = event.get("name")
        data = event.get("data")
        data_text = data if isinstance(data, str) else json.dumps(data or "")
        if tool_name == "terminal":
            if not isinstance(data, dict) or not isinstance(data.get("command"), str):
                return False
            command = data["command"]
            if "noisy_build.py" in command:
                script_commands.append(command)
            elif not command.startswith("echo "):
                return False
        elif tool_name in ("search_files", "read_file"):
            if "/cache/terminal-output" not in data_text:
                return False
            saw_spill_retrieval = True
        elif "noisy_build.py" in data_text:
            return False

    return (
        len(script_commands) == 1
        and script_commands[0].startswith("python3 ")
        and script_commands[0].endswith("/proj/noisy_build.pyc")
        and saw_spill_retrieval
    )


def read_events(trace_path: Path) -> list[dict[str, Any]]:
    if not trace_path.exists():
        return []
    events: list[dict[str, Any]] = []
    for line in trace_path.read_text(encoding="utf-8").splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if isinstance(event, dict):
            events.append(event)
    return events


def run_arm(
    *,
    arm: str,
    source_tree: Path,
    repetition: int,
    args: argparse.Namespace,
    hermes_home: Path,
) -> RunResult:
    run_id = f"{arm}-r{repetition}"
    run_root = args.output_root / "runs" / run_id
    if run_root.exists():
        shutil.rmtree(run_root)
    project = run_root / "proj"
    script = write_task(project)
    trace_path = args.output_root / "traces" / f"{run_id}.atof.jsonl"
    relay_config = run_root / "relay-plugins.toml"
    write_relay_config(trace_path, relay_config)

    query = (
        f"Run exactly `python3 {script}` once. Do not read or modify project files, "
        "rerun the command, or pipe or filter its output. Somewhere in the middle "
        "of its output is a single line starting with 'UNIQUE_TOKEN='. If the "
        "terminal reports truncation, use its suggested recovery path. Reply with "
        "the full token value."
    )
    environment = dict(os.environ)
    environment.update(
        {
            "PYTHONPATH": str(source_tree),
            "HERMES_HOME": str(hermes_home),
            "HERMES_NEMO_RELAY_PLUGINS_TOML": str(relay_config),
            "NVIDIA_BASE_URL": args.base_url,
        }
    )
    start = time.monotonic()
    try:
        completed = subprocess.run(
            [
                str(args.python),
                "-m",
                "hermes_cli.main",
                "chat",
                "--query",
                query,
                "--quiet",
                "--max-turns",
                "30",
                "--accept-hooks",
                "--model",
                args.model,
            ],
            cwd=run_root,
            env=environment,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            timeout=args.timeout_seconds,
        )
        response = completed.stdout or ""
        exit_code = completed.returncode
    except subprocess.TimeoutExpired:
        response = ""
        exit_code = -9

    llm_calls, tool_calls, result_bytes = trace_metrics(trace_path)
    return RunResult(
        arm=arm,
        run_id=run_id,
        exit_code=exit_code,
        llm_calls=llm_calls,
        tool_calls=tool_calls,
        tool_result_bytes=result_bytes,
        trace_valid_recovery=(
            exit_code == 0 and trace_valid_recovery(response, trace_path)
        ),
        wall_seconds=round(time.monotonic() - start, 1),
    )


def print_summary(results: list[RunResult]) -> None:
    print("\narm       n  valid recovery  mean LLM  mean tools  mean result KB  mean wall")
    print("-------------------------------------------------------------------------")
    for arm in ("baseline", "candidate"):
        rows = [result for result in results if result.arm == arm]
        count = len(rows)
        valid = 100 * sum(row.trace_valid_recovery for row in rows) / count
        print(
            f"{arm:9} {count:1d} {valid:14.0f}% "
            f"{sum(row.llm_calls for row in rows) / count:9.1f} "
            f"{sum(row.tool_calls for row in rows) / count:11.1f} "
            f"{sum(row.tool_result_bytes for row in rows) / count / 1024:14.0f} "
            f"{sum(row.wall_seconds for row in rows) / count:9.0f}s"
        )


def main() -> int:
    args = parse_args()
    args.output_root.mkdir(parents=True, exist_ok=True)
    hermes_home = args.output_root / "home"
    enable_relay_plugin(args.python, args.baseline, hermes_home)

    results: list[RunResult] = []
    for repetition in range(args.repetitions):
        arms = (
            (("baseline", args.baseline), ("candidate", args.candidate))
            if repetition % 2 == 0
            else (("candidate", args.candidate), ("baseline", args.baseline))
        )
        for arm, source_tree in arms:
            result = run_arm(
                arm=arm,
                source_tree=source_tree,
                repetition=repetition,
                args=args,
                hermes_home=hermes_home,
            )
            results.append(result)
            print(
                f"[{result.arm}] {result.run_id} exit={result.exit_code} "
                f"valid_recovery={result.trace_valid_recovery} "
                f"wall={result.wall_seconds:.0f}s",
                flush=True,
            )

    (args.output_root / "summary.json").write_text(
        json.dumps([asdict(result) for result in results], indent=2) + "\n",
        encoding="utf-8",
    )
    print_summary(results)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
