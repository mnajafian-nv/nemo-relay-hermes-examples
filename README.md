# Tracing Agent Harness Behavior with NVIDIA NeMo Relay

**Goal:** Trace a controlled Hermes Agent tool-use task with NVIDIA NeMo Relay,
then inspect the [Agent Trajectory Observability Format
(ATOF)](https://docs.nvidia.com/nemo/relay/latest/reference/atof-event-format)
event trace and [Agent Trajectory Interchange Format
(ATIF)](https://docs.nvidia.com/nemo/relay/configure-plugins/observability/atif)
trajectory from the run.

The included task asks Hermes to use its terminal tool to run
[`sample.py`](sample-project/sample.py) in an isolated Docker container and
return only `VALUE=42`. The script always prints that value, so the returned
result confirms that Hermes completed the expected task.

With the included Relay configuration, Hermes emits NeMo Relay lifecycle events
for its model calls and terminal-tool execution. Relay exports the run as an
ATOF trace and ATIF trajectory.

**In this tutorial, you will:**

1. Run Hermes with the included NeMo Relay configuration.
2. Run a fixed tool-use task with a deterministic success check.
3. Inspect how Hermes used the model and terminal tool to complete that task by
   comparing the raw ATOF trace with the ATIF trajectory.
4. Use the traces and task verifier to plan a focused evaluation of a change to
   the agent's tool-use behavior.

## Prerequisites

Before you start, complete the following prerequisites:

1. Use macOS or Linux.
2. Install [Git](https://git-scm.com/downloads).
3. Install and start [Docker](https://docs.docker.com/get-started/get-docker/).
4. Install Hermes Agent by using the [Hermes installation guide](https://hermes-agent.nousresearch.com/docs/getting-started/installation).
   This tutorial was verified with Hermes Agent `0.20.5` and NeMo Relay `0.7.2`.
   The runner verifies the Relay version before it starts.
5. Open [NVIDIA Build](https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b) for `nvidia/nemotron-3.5-lightning-30b-a3b`, then select **Generate API Key**.

**Success check:** `docker version` returns both client and server information.

For the pinned model and execution limits, see [config/smoke.env](config/smoke.env).

## How the Tutorial Runs

The runner creates an isolated Hermes home, renders the Relay configuration,
and uses Hermes' native, in-process Relay integration. It does not start the
Relay CLI or a local gateway.

The runner uses a constrained, ephemeral Docker container. It has no network
access, no checkout mount, a read-only root filesystem, a 128-process limit,
512 MiB of memory with no swap, and one CPU. It drops Linux capabilities,
prevents privilege escalation, does not pass `NVIDIA_API_KEY` to the
container, and does not fall back to Hermes' host-terminal default.

## Run the Tutorial

Clone the repository and create the local key file:

```bash
git clone https://github.com/mnajafian-nv/nemo-relay-hermes-examples.git
cd nemo-relay-hermes-examples
cp keys.env.example keys.env
```

Add the key you generated on NVIDIA Build to `keys.env`:

```text
NVIDIA_API_KEY=<your-nvidia-api-key>
```

The file is ignored by Git and keeps the key out of shell history. Build the
isolated tutorial image and run the task:

```bash
./scripts/build_tutorial_image.sh
./scripts/run_tutorial.sh
```

The runner creates an isolated Hermes home, renders a Relay configuration, and
runs a task that asks Hermes to execute the fixed sample script in the
tutorial container. The script prints `VALUE=42`.

**Success check:** Confirm that the output includes all of the following:

- `Task verified: VALUE=42`
- An ATOF summary with at least one completed LLM scope and tool call
- An ATIF summary with the agent, model, and trajectory step count
- `tool errors: 0`
- An `Artifacts:` path under `artifacts/runs/`

## Review the Run

The final output prints an `Artifacts:` path. That run directory contains:

- `atof/run.jsonl`, an [ATOF](https://docs.nvidia.com/nemo/relay/configure-plugins/observability/atof)
  capture of the raw, ordered lifecycle events.
- `atif/trajectory-*.json`, an [ATIF](https://docs.nvidia.com/nemo/relay/configure-plugins/observability/atif)
  trajectory that organizes those events into agent steps, tool calls, and
  observations.

The runner prints a summary of both files. To inspect their structure before
running the tutorial, open the minimal [example ATOF trace](examples/terminal-task.atof.jsonl),
[example ATIF trajectory](examples/terminal-task.atif.json), and [example walkthrough](examples/README.md).

### Inspect a Saved Run

The tutorial prints these summaries during the run. To print them again for a
saved run, replace `<run-directory>` with the path printed by the tutorial:

```bash
HERMES_PYTHON="$(sed -n '1s/^#!//p' "$(command -v hermes)")"
"$HERMES_PYTHON" scripts/summarize_atof.py \
  <run-directory>/atof/run.jsonl
"$HERMES_PYTHON" scripts/summarize_atif.py \
  <run-directory>/atif/trajectory-*.json
```

Treat the trace as diagnostic evidence, not the evaluator. Use the task's
mechanical acceptance check to determine whether it succeeded.

> [!CAUTION]
> Review traces before sharing them. They can contain prompts, tool arguments
> and results, file paths, model output, and other application data.

## Next Steps

Use the traces from a completed tutorial run to plan one controlled agent
change:

1. Replace [sample-project/sample.py](sample-project/sample.py) with a safe,
   fixed task that has a mechanical success check. Update `SMOKE_QUERY` and
   `SMOKE_EXPECTED_OUTPUT` in [config/smoke.env](config/smoke.env), then
   rebuild the tutorial image.
2. Capture several baseline runs with the same model, task fixture, execution limits, and verifier.
3. Use the traces to identify one repeated behavior, such as a retry, repeated file read, or tool error.
4. Change the component responsible for that behavior and run the same task and verifier again.
5. Compare task completion first. Then use model calls, tool calls, elapsed time, and errors to explain the result.

## Troubleshooting

### Authentication error

Confirm that `keys.env` contains a valid `NVIDIA_API_KEY` with access to the
model configured in [config/smoke.env](config/smoke.env).

### No trace files

Do not use `--safe-mode`; it prevents Hermes from loading the tutorial's Relay
configuration. The runner prints the output directory whenever it creates
trace files, even if the task later fails.

### Tutorial image unavailable

Run `./scripts/build_tutorial_image.sh`, then rerun the tutorial.

### Turn limit reached

Inspect the ATOF stream to determine whether the model, tool, or task prompt
caused the extra work.

## License

Apache-2.0. See [LICENSE](LICENSE).
