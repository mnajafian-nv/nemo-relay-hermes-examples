# Tracing Agent Harness Behavior with NVIDIA NeMo Relay

## Overview

An agent's final response does not tell you everything that happened during the
run. An incorrect result can come from missing context, a poor tool choice, or a
failed call. Even a correct result can hide repeated searches, unnecessary
retries, and extra model calls. Tracing the run helps you find these behaviors
and understand their effect on reliability, latency, and token usage.

[NVIDIA NeMo Relay](https://docs.nvidia.com/nemo/relay/latest/getting-started/about)
provides visibility into and control over agent runs without requiring changes
to the existing agent stack. It gives coding agents, applications, framework
integrations, middleware, and observability backends a shared runtime for
scopes, policy, plugins, and lifecycle events.

[Hermes Agent](https://github.com/NousResearch/hermes-agent) includes Relay on
supported platforms and maps its session, turn, LLM, and tool lifecycles to
Relay. This tutorial configures Relay exporters through that native integration.
It does not require a separate Hermes observability plugin, Relay CLI, or local
gateway.

This tutorial uses
[NVIDIA Nemotron 3.5 Lightning](https://build.nvidia.com/nvidia/nemotron-3.5-lightning-30b-a3b)
for two Hermes Agent runs.

**In this tutorial, you will:**

1. Set up an isolated Hermes Agent runtime with its native NeMo Relay
   integration.
2. Run the included Python script, verify its `VALUE=42` result, and inspect the
   agent's event stream and trajectory.
3. Ask Hermes to identify a conference from its dates, location, and subject,
   save the verified result in a report, and use Phoenix to inspect each step of
   the run.
4. Optionally trace the same conference task with another compatible model.
5. Use the trace evidence to evaluate a controlled prompt, tool, or harness
   change.

## Quick Start

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

## Continue with the Full Tutorial

After completing the Quick Start, continue with
[the detailed tutorial](TUTORIAL.md) to find and verify a conference with file
and web tools, then inspect each step of the agent's execution in Phoenix.

## License

This repository is licensed under the [Apache License 2.0](LICENSE).
