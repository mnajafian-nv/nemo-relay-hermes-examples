# Tracing Agent Harness Behavior with NVIDIA NeMo Relay

An agent can complete a coding task and still take an inefficient path. Repeated
searches, failed tool calls, and unnecessary retries are difficult to spot from
the final response alone, but they affect latency, token usage, and reliability.

This tutorial follows one deliberately simple Hermes Agent task with NVIDIA
[Nemotron 3.5 Lightning](https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b).
Hermes must use its terminal tool to run the included
[`sample.py`](sample-project/sample.py) script inside an isolated Docker
container and return the script's only output: `VALUE=42`. The value itself is
not the point. It gives the tutorial an exact pass/fail result, so the rest of
the walkthrough can focus on how Hermes completed the task.

[NVIDIA NeMo Relay](https://docs.nvidia.com/nemo/relay/latest/getting-started/about)
is an open-source agent runtime for execution scopes, lifecycle events,
middleware, plugins, and observability around model and tool calls. It can run
inside an agent or through its gateway.

In this tutorial, Relay runs inside Hermes through Hermes' native integration.
We use Relay only to represent Hermes' session, turn, model, and terminal-tool
execution as scopes and lifecycle events, then export that evidence through
ATOF and ATIF. The tutorial does not configure Relay middleware, guardrails, or
gateway routing.

The Agent Trajectory Observability Format
([ATOF](https://docs.nvidia.com/nemo/relay/latest/reference/atof-event-format))
exporter writes the ordered lifecycle event stream, while the Agent Trajectory
Interchange Format
([ATIF](https://docs.nvidia.com/nemo/relay/configure-plugins/observability/atif))
exporter turns the same events into a step-based trajectory. Together, they
show both the detailed execution sequence and the agent's path to the verified
result.

**In this tutorial, you will:**

1. Set up an isolated Hermes Agent and NeMo Relay environment.
2. Run a fixed terminal-tool task and verify its exact result.
3. Compare the ATOF trace and ATIF trajectory to understand the execution path
   and plan a controlled change to the agent's tool-use behavior.

## How the Tutorial Runs

The setup script creates a Git-ignored runtime under `.tutorial-runtime/` with
Hermes Agent `0.20.5` and NeMo Relay `0.7.2`. The runner creates a temporary
Hermes home and renders the Relay configuration without changing your existing
environment.

Hermes runs the terminal task in a constrained, ephemeral Docker container so
the model cannot execute commands in the host checkout. The container has no
network access or checkout mount, uses a read-only root filesystem and resource
limits, does not receive `NVIDIA_API_KEY`, and cannot fall back to the host
terminal.

## Run the Tutorial

On macOS or Linux, install [Git](https://git-scm.com/downloads), `curl`, and
[Docker](https://docs.docker.com/get-started/get-docker/). Start Docker and
create an API key for
[`nvidia/nemotron-3.5-lightning-30b-a3b`](https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b)
on NVIDIA Build.

Run the following commands in order. The `keys.env` file is ignored by Git and
keeps the key out of your shell history.

```bash
# Clone the tutorial repository.
git clone https://github.com/mnajafian-nv/nemo-relay-hermes-examples.git

# Enter the cloned repository.
cd nemo-relay-hermes-examples

# Create the isolated Hermes Agent and NeMo Relay runtime.
./scripts/setup_tutorial_runtime.sh

# Copy the API-key template.
cp keys.env.example keys.env

# Add NVIDIA_API_KEY to keys.env before continuing.

# Verify that Docker is running.
docker version

# Build the Docker image for the terminal-tool task.
./scripts/build_tutorial_image.sh

# Run the tutorial and export the ATOF and ATIF traces.
./scripts/run_tutorial.sh
```

**Success check:** Confirm that the output includes all of the following:

- `Task verified: VALUE=42`
- An ATOF summary with at least one completed LLM scope and tool call
- An ATIF summary with the agent, model, and trajectory step count
- `tool errors: 0`
- An `Artifacts:` path under `artifacts/runs/`

## Review the Run

The final output prints an `Artifacts:` path. That run directory contains:

- `atof/run.jsonl`, the raw, ordered lifecycle event stream.
- `atif/trajectory-*.json`, the run organized into agent steps, tool calls, and
  observations.

To inspect the file structure before running the tutorial, open the minimal
[example ATOF trace](examples/terminal-task.atof.jsonl),
[example ATIF trajectory](examples/terminal-task.atif.json), and
[example walkthrough](examples/README.md).

### Inspect a Saved Run

To summarize a saved run again, replace `<run-directory>` with the path printed
by the tutorial:

```bash
HERMES_PYTHON=".tutorial-runtime/venv/bin/python"
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

## Use the Traces to Evaluate a Change

1. Replace [sample-project/sample.py](sample-project/sample.py) with a safe,
   fixed task that has a mechanical success check. Update `SMOKE_QUERY` and
   `SMOKE_EXPECTED_OUTPUT` in [config/smoke.env](config/smoke.env), then
   rebuild the tutorial image.
2. Capture several baseline runs with the same model, task fixture, execution
   limits, and verifier.
3. Use the traces to identify one repeated behavior, such as a retry, repeated
   file read, or tool error.
4. Change the component responsible for that behavior and run the same task and
   verifier again.
5. Compare task completion first. Then use model calls, tool calls, elapsed
   time, and errors to explain the result.

## Troubleshooting

### Authentication Error

Confirm that `keys.env` contains a valid `NVIDIA_API_KEY` with access to the
model configured in [config/smoke.env](config/smoke.env).

### Tutorial Image Unavailable

Run `./scripts/build_tutorial_image.sh`, then rerun the tutorial.

### Turn Limit Reached

Inspect the ATOF stream to determine whether the model, tool, or task prompt
caused the extra work.

## License

Apache-2.0. See [LICENSE](LICENSE).
