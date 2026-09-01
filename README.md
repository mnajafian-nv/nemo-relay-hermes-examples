# Run a Hermes Task with NeMo Relay

**Goal:** Run a Hermes tool-use task through NVIDIA Inference, verify a known
task result, and inspect the NeMo Relay artifacts produced by the run.

**In this tutorial, you will:**

1. Install NeMo Relay in the Python environment that Hermes uses.
2. Run a deterministic task that asks Hermes to use the terminal.
3. Verify the task result, trace activity, and exported trajectory.
4. Use the trace as the starting point for a focused evaluation.

## Prerequisites

Before you start, complete the following prerequisites:

1. Use macOS or Linux.
2. Install Hermes Agent `0.20.5` or later by using the [Hermes installation guide](https://hermes-agent.nousresearch.com/docs/getting-started/installation).
3. Use Python 3.11 through 3.13 in the environment that provides the `hermes` command.
4. Have an NVIDIA Inference API key with access to `nvidia/nvidia/nemotron-3.5-lightning`.

For the pinned model and execution limits, see [config/smoke.env](config/smoke.env).

## About the Sample Task

The sample task is a minimal terminal-use workflow. Hermes receives an
instruction to run `python3 sample.py` from [sample-project](sample-project).
The script prints `VALUE=42`, and Hermes must return that exact line.

This creates one small, inspectable execution path: an LLM call selects the
terminal tool, the tool runs the local script, and Hermes returns the verified
result. The fixed output gives the runner a direct pass/fail check for the task
result and its Relay artifacts.

## Run the Tutorial

### Clone the Repository

Clone this repository:

```bash
git clone https://github.com/mnajafian-nv/nemo-relay-hermes-examples.git
cd nemo-relay-hermes-examples
```

### Install NeMo Relay

Install the version of NeMo Relay used by this tutorial in the Python environment that Hermes uses:

```bash
HERMES_PYTHON="${HERMES_PYTHON:-$(sed -n '1s/^#!//p' "$(command -v hermes)")}"
"$HERMES_PYTHON" -m pip install "nemo-relay==0.7.2"
"$HERMES_PYTHON" -c 'from importlib.metadata import version; print(version("nemo-relay"))'
```

**Success check:** The last command prints `0.7.2`.

### Configure NVIDIA Inference Access

Copy the environment file and add your API key:

```bash
cp keys.env.example keys.env
```

Set `NVIDIA_API_KEY` in `keys.env`. The file is Git-ignored, and using it keeps the key out of shell history.

### Run and Verify the Task

Run the tutorial:

```bash
./scripts/run_tutorial.sh
```

The runner creates an isolated Hermes home, renders a Relay configuration, and
runs a task that asks Hermes to execute `python3 sample.py`. The script prints
`VALUE=42`.

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

1. Replace [sample-project/sample.py](sample-project/sample.py) with a safe, deterministic task that has a mechanical success check.
2. Capture several baseline runs with the same model, task fixture, execution limits, and verifier.
3. Use the traces to identify one repeated behavior, such as a retry, repeated file read, or tool error.
4. Change the component responsible for that behavior and run the same task and verifier again.
5. Compare task completion first. Then use model calls, tool calls, elapsed time, and errors to explain the result.

## Troubleshoot the Tutorial

### Authentication fails

Confirm that `NVIDIA_API_KEY` is set in `keys.env` and can access the model in [config/smoke.env](config/smoke.env).

### No artifacts are written

Do not use `--safe-mode`, because it prevents Hermes from loading the tutorial's Relay configuration. The runner prints the artifact directory whenever it creates artifacts, even if the task later fails.

### Hermes reaches its turn limit

The runner marks the task as failed. Inspect the ATOF stream to determine whether the model, tool, or task prompt caused the extra work.

<details>
<summary>Validate repository changes</summary>

These checks use synthetic events and do not call a model or require an API
key.

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/render_relay_config.py scripts/summarize_atof.py scripts/summarize_atif.py
bash -n scripts/check_environment.sh scripts/run_tutorial.sh
```

</details>

## License

Apache-2.0. See [LICENSE](LICENSE).
