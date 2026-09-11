# Tracing Agent Harness Behavior with NVIDIA NeMo Relay

## Overview

An agent's final response does not tell you everything that happened during the
run. An incorrect result can come from missing context, a poor tool choice, or a
failed call. Even a correct result can hide repeated searches, unnecessary
retries, and extra model calls. Tracing the run helps you find these behaviors
and understand their effect on reliability, latency, and token usage.

[NVIDIA NeMo Relay](https://docs.nvidia.com/nemo/relay/latest/about-nemo-relay/overview)
provides visibility into and control over agent runs without requiring changes
to the existing agent stack. It gives coding agents, applications, framework
integrations, middleware, and observability backends a shared runtime for
scopes, policy, plugins, and lifecycle events.

[Hermes Agent](https://hermes-agent.nousresearch.com/) understands NeMo Relay
plugin configurations. NeMo Relay is built into Hermes Agent, so no separate
observability plugin or Relay CLI setup is required. This tutorial uses that
built-in integration to load Relay exporters without starting a local gateway.

This tutorial uses
[NVIDIA Nemotron 3.5 Lightning](https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b)
in two examples. The first verifies the setup with a fixed terminal task. The
second uses file and web tools to identify a conference and opens the resulting
trace in [Arize Phoenix](https://arize.com/phoenix/).

**In this tutorial, you will:**

1. Set up an isolated Hermes Agent runtime with its native NeMo Relay
   integration.
2. Run a fixed terminal task and inspect its Agent Trajectory Observability Format
   ([ATOF](https://docs.nvidia.com/nemo/relay/latest/configure-plugins/observability/atof))
   event stream and Agent Trajectory Interchange Format
   ([ATIF](https://docs.nvidia.com/nemo/relay/latest/configure-plugins/observability/atif))
   trajectory.
3. Run a file-and-web research task and explore its OpenTelemetry trace in
   Phoenix.
4. Use the traces and verifier to evaluate one controlled prompt, tool, or
   harness change.

## Quick Start

### Set Up the Tutorial

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

### Example 1: Run and Trace a Terminal Task

Verify Docker, build the task image, and run the tutorial:

```bash
# Confirm that the Docker client can reach the Docker service.
docker version

# Build the Docker image for the terminal-tool task.
./scripts/build_tutorial_image.sh

# Run the task and export the ATOF event stream and ATIF trajectory.
./scripts/run_tutorial.sh
```

**What you should see:** Hermes returns `VALUE=42`. The runner then validates
the trace and prints the ATOF and ATIF summaries. One verified run ended with:

```text
ATOF summary:
trace: .../artifacts/runs/<run-id>/atof/run.jsonl
events: 74
completed llm scopes: 2
llm scopes with usage: 2
prompt tokens: 7239
completion tokens: 96
total tokens: 7335
tool calls: 1
tool errors: 0
correlated events: 74

ATIF summary:
trajectory: .../artifacts/runs/<run-id>/atif/trajectory-<session-id>.json
agent: Hermes Agent
model: nvidia/nemotron-3.5-lightning-30b-a3b
steps: 3
llm calls: 2
requested tool calls: 1

Task verified: VALUE=42

Artifacts: .../artifacts/runs/<run-id>
```

The counts, identifiers, and run directory vary between runs. The runner exits
with an error if the result or trace validation fails.

### Why the Task Runs in Docker

Hermes can execute terminal commands, so this tutorial runs them in an isolated
Docker container instead of on your host. The container cannot access the
network, repository checkout, or NVIDIA API key.

## Continue to Example 2

Example 2 reuses the runtime created during the Quick Start. Continue with
[the detailed tutorial](TUTORIAL.md) to identify and verify a conference with
file and web tools, then inspect the agent run in Phoenix.

## Source Repositories

- [NVIDIA NeMo Relay](https://github.com/NVIDIA/NeMo-Relay)
- [Hermes Agent](https://github.com/NousResearch/hermes-agent)

## License

This repository is licensed under the [Apache License 2.0](LICENSE).
