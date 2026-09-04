# Tracing Agent Harness Behavior with NVIDIA NeMo Relay

An agent can complete a coding task and still take an inefficient path. Repeated
searches, failed tool calls, and unnecessary retries are difficult to spot from
the final response alone, but they affect latency, token usage, and reliability.

This tutorial follows one deliberately simple Hermes Agent task with Claude
Sonnet 5 served through NVIDIA Inference. Hermes must use its terminal tool to
run the included [`sample.py`](sample-project/sample.py) script inside an
isolated Docker container and return the script's only output: `VALUE=42`. The
value itself is not the point. It gives the tutorial an exact pass/fail result,
so the rest of the walkthrough can focus on how Hermes completed the task.

[NVIDIA NeMo Relay](https://docs.nvidia.com/nemo/relay/latest/getting-started/about)
is an open-source, multi-language agent runtime framework that provides a
shared execution model for scopes, managed tool and LLM calls, asynchronous
middleware, plugin lifecycles, adaptive caching, and lifecycle observability.

In this tutorial, Relay runs inside Hermes through Hermes' native integration.
It represents the session, turn, model, and terminal-tool lifecycles as ATOF
events and an ATIF trajectory. The tutorial does not configure Relay
middleware, guardrails, or gateway routing.

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
obtain an NVIDIA Inference API key authorized for
`aws/anthropic/bedrock-claude-sonnet-5`. This is an NVIDIA-hosted model endpoint;
an NVIDIA Build API key does not authenticate this configuration.

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

## Optional Exercise: Trace a Multi-Tool Research Task in Phoenix

The first exercise isolates one terminal call. This follow-up shows a more
realistic agent path across files and the web. Hermes reads a fixed
[conference travel record](conference-task/travel-record.md), identifies the
event that matches every constraint, verifies it on the official conference
website, and saves a verification report.

Relay exports the run as ATOF, ATIF, and an
[OpenInference trace](https://docs.nvidia.com/nemo/relay/latest/configure-plugins/observability/openinference)
for [Arize Phoenix](https://arize.com/docs/phoenix). Complete the first exercise
before running this one so the isolated Hermes runtime and tutorial Docker image
are available.

No separate Phoenix installation is required. The exercise downloads the
pinned Phoenix container image if needed and starts it locally. If port `6006`
is already in use, use the alternate-port command below. The script does not
stop or replace the existing service.

```bash
# Research the conference and inspect the file, web, and model path in Phoenix.
./scripts/run_conference_research_with_phoenix.sh
```

Hermes uses its built-in keyless web search, so no Tavily key or other search
credential is required. The runner verifies all of the following:

- The final answer identifies the expected conference.
- The saved verification report contains the dates, location, and official
  source.
- The ATOF trace contains successful `read_file`, `web_search`, `web_extract`,
  and `write_file` calls.
- ATIF contains the trajectory, and Phoenix receives the corresponding model
  and tool spans.
- Phoenix calculates positive token and estimated-cost totals for the trace.

The script prints a Phoenix URL and saves the response, verification report,
ATOF events, and ATIF trajectory under `artifacts/conference-research/`. The
fixed input is mounted read-only, a separate output directory is mounted
read/write, writes are restricted to `/output`, and your API key is not passed
to the tool container.

Open the printed Phoenix URL, select the project named in the verification
output, and expand its trace. Follow the `read_file`, `web_search`,
`web_extract`, and `write_file` spans to see how Hermes moved from the travel
record to the saved report. Compare that view with the ATOF and ATIF summaries
printed by the runner.

### Phoenix Walkthrough

The expanded trace view shows the complete execution path with model and tool
spans, per-span durations, token counts, and the total estimated cost. The
verified run below completed the research task with five model calls, five tool
calls, no tool errors, 59,704 priced tokens, and an estimated cost of
`$0.042031`.

![Phoenix trace tree with model, file, and web spans](screenshots/phoenix-trace-tree.png)

Select a tool span to inspect the request and result that moved the agent from
the task constraints to the verified answer.

![Phoenix web-search span with query and results](screenshots/phoenix-web-search-span.png)

Phoenix uses port `6006` by default. If that port is unavailable, choose another
local port:

```bash
PHOENIX_UI_PORT=6007 ./scripts/run_conference_research_with_phoenix.sh
```

Phoenix data remains in the tutorial container until you remove it:

```bash
# Stop Phoenix and delete the tutorial container and its local trace data.
./scripts/stop_phoenix.sh
```

If you selected another port, pass the same value when removing the container,
for example `PHOENIX_UI_PORT=6007 ./scripts/stop_phoenix.sh`.

The keyless search providers are public services and can be rate-limited. The
runner fails if Hermes does not complete a real `web_search`; it does not accept
an answer based only on model knowledge.

## Apply This Approach to Your Agent

1. Define a fixed task with a mechanical success check.
2. Run it several times with the model, prompt, tools, and execution limits held
   constant.
3. Use the Relay traces to identify one repeated failure or inefficiency.
4. Make one focused change to the responsible prompt, tool configuration, or
   harness behavior.
5. Run the same task again under the same conditions.
6. Compare task completion first, then use model calls, tool calls, errors, and
   elapsed time to explain the result.

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
