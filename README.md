# Hermes and NeMo Relay examples

This is a private working lab. Promote only the validated tutorial subset to the
shared blog repository after the model, Hermes release, and publication claim
are agreed.

This repository accompanies an upcoming tutorial that shows how to run a Hermes coding-agent task with a model hosted on NVIDIA Inference and NeMo Relay, inspect the resulting trace, and use that evidence to evaluate a focused harness change.

The repository intentionally keeps the first path small:

1. Run a local Hermes task through an NVIDIA-hosted model.
2. Enable NeMo Relay with a minimal plugin configuration.
3. Verify that the task result and Relay telemetry were produced.

The optional evaluation path compares a baseline and a trace-motivated change on deterministic tasks. It does not claim that enabling Relay itself improves an agent. Relay supplies the execution evidence used to choose and validate a change.

## Prerequisites

- Python 3.11 or later
- Hermes Agent `0.20.5`
- `nemo-relay` `0.7.2` in the Python environment Hermes uses
- An NVIDIA Inference API key with access to `nvidia/qwen/qwen3.5-9b`

The supported smoke contract is pinned in
[config/smoke.env](config/smoke.env). `scripts/check_environment.sh` verifies
the installed Hermes and NeMo Relay versions before the run starts.

## Quick start

1. Copy the environment template and set your key locally:

   ```bash
   cp keys.env.example keys.env
   # Edit keys.env and set NVIDIA_API_KEY. Do not commit this file.
   ```

2. Validate the local prerequisites:

   ```bash
   ./scripts/check_environment.sh
   ```

3. Run the included deterministic smoke task:

   ```bash
   ./scripts/run_smoke_evaluation.sh
   ```

The script runs Hermes through NVIDIA Inference's OpenAI-compatible endpoint, `https://inference-api.nvidia.com/v1`, in an isolated local home beneath `/tmp/nemo-relay-hermes-examples`. A successful run prints `VALUE=42` and produces a Hermes session log plus Relay ATOF and ATIF outputs.

## Evaluation method

The evaluation plan and result format are documented in
[evaluation/README.md](evaluation/README.md). Record the task manifest before
running a comparison. Use the same model, provider settings, task budget, and
execution environment for baseline and candidate runs. The checked-in result
ledger records completed experiments, including inconclusive ones.

## Safety and privacy

The included Relay configuration disables full payload capture. Do not commit API keys, raw prompts, tool output, traces, or task artifacts that can contain sensitive data.

## Status

The Qwen smoke configuration has passed the end-to-end contract: Hermes
executes the terminal call, returns `VALUE=42`, and Relay writes ATOF and ATIF
artifacts. A focused exploratory trial also reduced average LLM and tool calls,
but did not establish a latency or cost improvement. This repository does not
make a performance claim until a reproducible baseline/candidate comparison
supports one.
