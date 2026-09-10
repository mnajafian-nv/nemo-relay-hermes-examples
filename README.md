# Tracing Agent Harness Behavior with NVIDIA NeMo Relay

An agent's final response does not tell you everything that happened during the
run. An incorrect result can come from missing context, a poor tool choice, or a
failed call. Even a correct result can hide repeated searches, unnecessary
retries, and extra model calls. Tracing the run helps you find these behaviors
and understand their effect on reliability, latency, and token usage.

[NVIDIA NeMo Relay](https://docs.nvidia.com/nemo/relay/latest/getting-started/about)
is an open-source, multi-language agent runtime framework for scope management,
managed tool and LLM calls, middleware, plugins, caching, and lifecycle
observability. Hermes Agent includes Relay natively. Its integration maps
sessions, turns, model calls, and tool calls to Relay scopes and lifecycle
events.

This tutorial follows two Hermes Agent runs with
[NVIDIA Nemotron 3.5 Lightning](https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b).
First, Hermes runs the included [`sample.py`](sample-project/sample.py) script
inside an isolated Docker container and returns its only output: `VALUE=42`.
That exact output verifies the task result. Next, Hermes uses file and web tools
to research a conference and save a verified report. NeMo Relay exports an
Agent Trajectory Observability Format
([ATOF](https://docs.nvidia.com/nemo/relay/latest/reference/atof-event-format))
event stream and an Agent Trajectory Interchange Format
([ATIF](https://docs.nvidia.com/nemo/relay/latest/configure-plugins/observability/atif))
trajectory for each run. For the research task, Relay also sends
[OpenInference](https://docs.nvidia.com/nemo/relay/latest/configure-plugins/observability/openinference)
spans over OTLP to [Arize Phoenix](https://arize.com/docs/phoenix), where you can
inspect the model and tool calls, token usage, duration, and errors.

**In this tutorial, you will:**

1. Set up an isolated Hermes Agent runtime with its native NeMo Relay
   integration.
2. Run a fixed terminal-tool task, verify the result, and inspect its ATOF
   event stream and ATIF trajectory.
3. Run a file-and-web research task and inspect its model calls, tool calls,
   duration, token usage, and any estimated cost reported by Phoenix.
4. Optionally inspect the Claude Sonnet 5 example or repeat the research task
   with another compatible model.
5. Use the same task and model settings to compare one prompt, tool, or harness
   change.

## Run the Tutorial

The setup script creates `.tutorial-runtime/` and installs Hermes Agent `0.21.1`
with the NeMo Relay `0.8.3` version pinned by Hermes. It does not change your
existing Hermes installation.

Before you begin:

- Use macOS or Linux.
- Install [Git](https://git-scm.com/downloads),
  [curl](https://curl.se/download.html), and
  [Docker](https://docs.docker.com/get-started/get-docker/), and start Docker.
- Generate an API key from the
  [Nemotron 3.5 Lightning model page](https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b)
  on NVIDIA Build.

Clone the repository and create the isolated runtime:

```bash
# Clone the tutorial repository.
git clone https://github.com/mnajafian-nv/nemo-relay-hermes-examples.git

# Enter the cloned repository.
cd nemo-relay-hermes-examples

# Create the isolated Hermes Agent and NeMo Relay runtime.
./scripts/setup_tutorial_runtime.sh

# Copy the API-key template.
cp keys.env.example keys.env
```

Open `keys.env` and set `NVIDIA_API_KEY` to the key you generated. The repository
ignores this file, and editing it keeps the key out of your shell history.

```ini
NVIDIA_API_KEY=<your-nvidia-api-key>
```

Verify Docker, build the task image, and run the tutorial:

```bash
# Confirm that the Docker client can reach the Docker service.
docker version

# Build the Docker image for the terminal-tool task.
./scripts/build_tutorial_image.sh

# Run the task and export the ATOF event stream and ATIF trajectory.
./scripts/run_tutorial.sh
```

**Success check:** Confirm that the output includes all of the following:

- `Task verified: VALUE=42`
- An ATOF summary with at least one completed LLM scope, a token total greater
  than zero, and one tool call
- An ATIF summary with the agent, model, and trajectory step count
- `tool errors: 0`
- An `Artifacts:` path under `artifacts/runs/`

### Why the Tutorial Uses Docker

Hermes can execute terminal commands, so this tutorial runs them in an isolated
Docker container instead of on your host. The container cannot access the
network, repository checkout, or NVIDIA API key.

## Continue the Tutorial

Continue with [Trace Hermes Agent Runs with NeMo Relay](TUTORIAL.md) to:

- inspect the ATOF event stream and ATIF trajectory from the terminal task;
- run the multi-tool research task and inspect its OpenInference spans in
  Phoenix;
- repeat the research task with another compatible model; and
- evaluate a controlled prompt, tool, or harness change.

The detailed guide also includes the verified Nemotron result, Phoenix
screenshots, trace-reading guidance, and troubleshooting steps.

## License

This repository is licensed under the [Apache License 2.0](LICENSE).
