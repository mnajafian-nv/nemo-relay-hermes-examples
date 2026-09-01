# Hermes and NeMo Relay examples

This is a working lab. Promote only the validated tutorial subset to the shared
blog repository after the model, Hermes release, and publication claim are
agreed.

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
- An NVIDIA Inference API key with access to `nvidia/nvidia/nemotron-3.5-lightning`

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

## Trace-validated recovery case

The included focused case study evaluates a Hermes terminal-output recovery
change. The fixture deletes its own source when it starts, so a successful run
must recover the answer from terminal output rather than inspect the task
source. Relay verifies that behavior from the trace: one terminal execution,
then retrieval from the candidate's spill artifact.

Five alternating baseline/candidate pairs with
`nvidia/nvidia/nemotron-3.5-lightning` produced 0/5 trace-valid recoveries for
the baseline and 5/5 for the candidate. Mean wall time was 88 seconds for the
baseline and 13 seconds for the candidate. This is a focused correctness and
latency result, not a general agent benchmark or a cost claim. See
[evaluation/README.md](evaluation/README.md) to reproduce the case and
[evaluation/results.md](evaluation/results.md) for the complete protocol and
result ledger.

## Evaluation method

The evaluation plan and result format are documented in
[evaluation/README.md](evaluation/README.md). Record the task manifest before
running a comparison. Use the same model, provider settings, task budget, and
execution environment for baseline and candidate runs. The checked-in result
ledger records completed experiments, including inconclusive ones.

## Safety and privacy

The included Relay configuration disables full payload capture. Do not commit API keys, raw prompts, tool output, traces, or task artifacts that can contain sensitive data.

## Status

The NVIDIA Nemotron smoke configuration has passed the end-to-end contract:
Hermes executes the terminal call, returns `VALUE=42`, and Relay writes ATOF
and ATIF artifacts. The trace-validated output-recovery case has also passed
its five-pair protocol. Earlier exploratory cases are retained in the result
ledger as rejected evidence so readers can see why the selected case has a
stronger verifier.
