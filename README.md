# Run a Hermes Task with NeMo Relay

**Goal:** Run a Hermes tool-use task through NVIDIA Inference, verify a known
task result, and inspect the NeMo Relay artifacts produced by the run.

**Validated with:** Hermes Agent `0.21.0` and its bundled NeMo Relay `0.7.2`.

**In this tutorial, you will:**

1. Use the NeMo Relay version bundled with Hermes Agent.
2. Run a fixed task with a deterministic success check.
3. Verify the task result, trace activity, and exported trajectory.
4. Use the trace as the starting point for a focused evaluation.

## Prerequisites

Before you start, complete the following prerequisites:

1. Use macOS or Linux.
2. Install Hermes Agent `0.21.0` by using the [Hermes installation guide](https://hermes-agent.nousresearch.com/docs/getting-started/installation). It bundles NeMo Relay `0.7.2` for this tutorial.
3. Have an [NVIDIA API key](https://build.nvidia.com/nvidia/llama-3_3-nemotron-super-49b-v1_5) authorized to use `llama-3.3-nemotron-super-49b-v1.5`.
4. Install and start [Docker](https://docs.docker.com/get-started/get-docker/).

**Success check:** `docker version` returns both client and server information.

For the pinned model and execution limits, see [config/smoke.env](config/smoke.env).

## About the Sample Task

The sample task is a minimal terminal-use workflow. Hermes receives an
instruction to run a fixed script from [sample-project](sample-project) in the
tutorial image. The script prints `VALUE=42`, and Hermes must return that
exact line.

This creates one small, inspectable execution path: an LLM call selects the
terminal tool, Hermes is asked to run the fixed script in a tutorial Docker
image, and Hermes returns the verified result. The runner verifies the returned output,
terminal activity in the Relay trace, and a terminal command that references
`sample.py`.

The runner uses a constrained, ephemeral Docker container. It has no network
access, no checkout mount, a read-only root filesystem, a 128-process limit,
512 MiB of memory with no swap, and one CPU. It drops Linux capabilities,
prevents privilege escalation, does not pass `NVIDIA_API_KEY` to the
container, and does not fall back to Hermes' host-terminal default.

## Run the Tutorial

### Clone the Repository

Clone this repository:

```bash
git clone https://github.com/mnajafian-nv/nemo-relay-hermes-examples.git
cd nemo-relay-hermes-examples
```

### Use Hermes' Bundled NeMo Relay

Hermes Agent `0.21.0` bundles NeMo Relay `0.7.2` on the supported platforms
used by this tutorial. Do not install a separate Relay package into the Hermes
environment. The runner verifies both versions before it starts the task.

### Configure NVIDIA Inference Access

Copy the environment file and add your API key:

```bash
cp keys.env.example keys.env
```

Set `NVIDIA_API_KEY` in `keys.env`. The file is Git-ignored, and using it keeps the key out of shell history.

### Build the Tutorial Image

Build the image that contains only the fixed sample task:

```bash
./scripts/build_tutorial_image.sh
```

### Run and Verify the Task

Run the tutorial:

```bash
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

## Inspect the Artifacts

The runner stores task output and two complementary Relay artifacts in the
artifact directory. It does not retain Hermes authentication or runtime state.

Before running the tutorial, you can inspect the paired [example ATOF trace](examples/terminal-task.atof.jsonl)
and [example ATIF trajectory](examples/terminal-task.atif.json). The
[example walkthrough](examples/README.md) shows how the same terminal task is
represented in each format.

- [ATOF](https://docs.nvidia.com/nemo/relay/configure-plugins/observability/atof)
  is the canonical raw JSONL event stream. Use it to diagnose a specific run
  and inspect exact LLM, tool, and lifecycle events.
- [ATIF](https://docs.nvidia.com/nemo/relay/configure-plugins/observability/atif)
  is a trajectory projection assembled from related ATOF events. Use it for a
  step-oriented view of the agent run and offline analysis, replay, or evaluation.

### Inspect ATOF

Run the ATOF summarizer again by replacing `<artifact-directory>` with the
path printed by the tutorial:

```bash
HERMES_PYTHON="$(sed -n '1s/^#!//p' "$(command -v hermes)")"
"$HERMES_PYTHON" scripts/summarize_atof.py \
  <artifact-directory>/atof/run.jsonl
```

### Inspect ATIF

Run the ATIF summarizer:

```bash
HERMES_PYTHON="$(sed -n '1s/^#!//p' "$(command -v hermes)")"
"$HERMES_PYTHON" scripts/summarize_atif.py \
  <artifact-directory>/atif/trajectory-*.json
```

<details>
<summary>Print the raw ATIF trajectory</summary>

```bash
HERMES_PYTHON="$(sed -n '1s/^#!//p' "$(command -v hermes)")"
"$HERMES_PYTHON" -m json.tool \
  <artifact-directory>/atif/trajectory-*.json
```

</details>

| Question | Where to look |
| --- | --- |
| Did the task finish? | `VALUE=42` and an exported ATIF trajectory file. |
| How much LLM and tool activity occurred? | The printed ATOF summary. |
| Which model and tools ran? | The raw ATOF event stream. |
| How did the agent progress through the task? | The ATIF trajectory. |
| Did a tool fail? | `tool errors` and the raw ATOF events. |

> [!CAUTION]
> Review artifacts before sharing them. They can contain prompts, tool arguments
> and results, file paths, model output, and other application data.

## Next Steps

Use the artifacts from a completed tutorial run to plan one controlled agent
change:

1. Replace [sample-project/sample.py](sample-project/sample.py) with a safe,
   fixed task that has a mechanical success check. Update `SMOKE_QUERY` and
   `SMOKE_EXPECTED_OUTPUT` in [config/smoke.env](config/smoke.env), then
   rebuild the tutorial image.
2. Capture several baseline runs with the same model, task fixture, execution limits, and verifier.
3. Use the traces to identify one repeated behavior, such as a retry, repeated file read, or tool error.
4. Change the component responsible for that behavior and run the same task and verifier again.
5. Compare task completion first. Then use model calls, tool calls, elapsed time, and errors to explain the result.

## Troubleshoot the Tutorial

### Authentication fails

Confirm that `NVIDIA_API_KEY` is set in `keys.env` and can access the model in [config/smoke.env](config/smoke.env).

### No artifacts are written

Do not use `--safe-mode`, because it prevents Hermes from loading the tutorial's Relay configuration. The runner prints the artifact directory whenever it creates artifacts, even if the task later fails.

### The tutorial image is missing

Run `./scripts/build_tutorial_image.sh`, then rerun the tutorial.

### Hermes reaches its turn limit

The runner marks the task as failed. Inspect the ATOF stream to determine whether the model, tool, or task prompt caused the extra work.

<details>
<summary>Validate repository changes</summary>

These checks use synthetic events and do not call a model or require an API
key.

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/render_relay_config.py scripts/summarize_atof.py scripts/summarize_atif.py
bash -n scripts/build_tutorial_image.sh scripts/check_environment.sh \
  scripts/configure_tutorial_terminal.sh scripts/run_tutorial.sh
```

</details>

## License

Apache-2.0. See [LICENSE](LICENSE).
