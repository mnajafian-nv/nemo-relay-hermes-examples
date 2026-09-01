# Hermes + NeMo Relay quickstart

Run one Hermes task through NVIDIA Inference and inspect the NeMo Relay trace it
produces. This repository is a small, runnable example of local agent
observability, not a benchmark or a performance comparison.

## What this run proves

The smoke task asks Hermes to execute `python3 sample.py` exactly once. A
successful run proves that:

- Hermes can call the configured NVIDIA-hosted model and terminal tool.
- NeMo Relay captures the run.
- Relay writes both ATOF events and an ATIF trajectory locally.

The task returns `VALUE=42`. It is deliberately small so the trace is easy to
read.

## Requirements

- A macOS or Linux shell
- Python 3.11 or later
- Hermes Agent `0.20.5`
- An NVIDIA Inference API key with access to
  `nvidia/nvidia/nemotron-3.5-lightning`

The supported versions and model are pinned in
[config/smoke.env](config/smoke.env).

## Install Hermes and Relay

Install Hermes with the [official Hermes installation guide](https://hermes-agent.nousresearch.com/docs/getting-started/installation).
Then install the pinned Relay package into the Python environment used by the
`hermes` command:

```bash
HERMES_PYTHON="$(sed -n '1s/^#!//p' "$(command -v hermes)")"
"$HERMES_PYTHON" -m pip install "nemo-relay==0.7.2"
```

`./scripts/check_environment.sh` confirms that Hermes and Relay use the pinned
versions before the task starts.

## Run it

1. Create a local credentials file:

   ```bash
   cp keys.env.example keys.env
   ```

   Set `NVIDIA_API_KEY` in `keys.env`. The file is ignored by Git.

2. Confirm the environment:

   ```bash
   ./scripts/check_environment.sh
   ```

3. Run the task:

   ```bash
   ./scripts/run_smoke_evaluation.sh
   ```

The expected response is:

```text
VALUE=42
```

## Inspect the trace

The runner uses an isolated Hermes home and writes all artifacts beneath
`/tmp/nemo-relay-hermes-examples` by default:

```text
/tmp/nemo-relay-hermes-examples/
  hermes-output.txt
  relay/
    atof/run.jsonl
    atif/trajectory-<session-id>.json
```

Use the included inspector to view the lifecycle without reading raw JSONL:

```bash
python3 scripts/inspect_smoke_trace.py \
  /tmp/nemo-relay-hermes-examples/relay/atof/run.jsonl
```

The timeline should show a `hermes.session`, one `hermes.turn`, LLM calls, and
one `terminal` scope. The raw ATOF stream is useful when you need individual
events; the ATIF file is the assembled agent trajectory.

```text
hermes.session
  hermes.turn
    hermes.logical_llm_call
      openai.chat_completions
      terminal
```

Treat every trace as sensitive until you inspect and sanitize it. Do not commit
raw traces, logs, prompts, tool output, or credentials from a real workload.

## What this example does not claim

Relay records evidence about an agent run. It does not itself make an agent
faster, cheaper, or more accurate. The `evaluation/` directory contains
experimental harness work that is not part of this quickstart and does not
support a public performance claim.

## Next step

Replace `sample-project/sample.py` with a safe task of your own, rerun the
example, and use the ATOF or ATIF output to understand the agent's execution
path.
