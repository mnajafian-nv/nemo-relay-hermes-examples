# Capture a Hermes Trace with NeMo Relay

**Goal:** Run a tool-using Hermes task through NVIDIA Inference, verify the
result, and inspect the NeMo Relay trace produced on your machine.

> **Note:** This tutorial shows how to capture evidence about an agent run. It
> does not benchmark or claim an improvement to agent quality, latency, or cost.

## In This Tutorial, You Will

1. Configure a local Hermes and NeMo Relay environment.
2. Run a deterministic task with Relay enabled.
3. Verify the task result and Relay artifacts.
4. Read the trace summary to identify model calls, tool calls, and tool errors.

The task runs `python3 sample.py`, which prints `VALUE=42`. It is deliberately
small so the result is unambiguous and the trace is easy to inspect.

## Prerequisites

Before you start, complete the following prerequisites:

1. Use macOS or Linux with Hermes Agent `0.20.5` or later.
2. Use Python 3.11 or later in the Python environment behind `hermes`.
3. Obtain an NVIDIA Inference API key with access to
   `nvidia/nvidia/nemotron-3.5-lightning`.
4. Install NeMo Relay `0.7.2` in Hermes's Python environment:

   ```bash
   HERMES_PYTHON="$(sed -n '1s/^#!//p' "$(command -v hermes)")"
   "$HERMES_PYTHON" -m pip install "nemo-relay==0.7.2"
   ```

Install Hermes with the [official installation guide](https://hermes-agent.nousresearch.com/docs/getting-started/installation). The tested model, Relay version, and execution limits are in
[config/smoke.env](config/smoke.env).

Hermes owns the Relay runtime in this release. Do not enable the removed
`observability/nemo_relay` Hermes plugin.

## Tutorial Steps

Work through each step in order. The runner creates an isolated Hermes home
for every execution and removes it when the run finishes, so it does not modify
your normal Hermes configuration or retain Hermes runtime state with the trace.

### Run the Task with Relay Enabled

1. Clone the repository and set your NVIDIA Inference API key:

   ```bash
   git clone https://github.com/mnajafian-nv/nemo-relay-hermes-examples.git
   cd nemo-relay-hermes-examples
   export NVIDIA_API_KEY="<your NVIDIA Inference API key>"
   ```

   To keep the key out of your shell history, copy
   [keys.env.example](keys.env.example) to `keys.env` and set
   `NVIDIA_API_KEY` there. The file is ignored by Git.

2. Run the tutorial:

   ```bash
   ./scripts/run_tutorial.sh
   ```

   The runner renders a Relay `plugins.toml`, starts Hermes with that file,
   runs the sample task, verifies the final answer, and writes ATOF and ATIF
   artifacts under `artifacts/runs/` in the cloned repository by default. The
   retained directory contains only the task output and Relay artifacts, not
   Hermes authentication or runtime state. It is ignored by Git. Set
   `RUNTIME_ROOT` to store artifacts elsewhere.

**✅ Success Check:** The command prints `Task verified: VALUE=42`, reports a
nonzero number of completed LLM scopes and tool calls, reports `tool errors: 0`,
and ends with the local `Artifacts:` directory.

### Inspect the Trace

The runner prints a summary automatically. Run the summarizer again by using
the artifact directory from the previous step:

```bash
HERMES_PYTHON="$(sed -n '1s/^#!//p' "$(command -v hermes)")"
"$HERMES_PYTHON" scripts/summarize_atof.py \
  <artifact-directory>/atof/run.jsonl
```

| Question | Trace evidence |
| --- | --- |
| Did the task finish? | `VALUE=42` and a completed ATIF trajectory. |
| Did Hermes call a model? | `completed llm scopes` is nonzero. |
| Did Hermes call a tool? | `tool calls` is nonzero. |
| Did a tool report failure? | Review `tool errors` and the raw ATOF events. |

ATOF is Relay's event stream. ATIF is the completed agent trajectory assembled
from that stream.

**✅ Success Check:** You can identify the completed LLM scopes, terminal tool
calls, and tool-error count without reading each JSONL event manually.

### Apply the Pattern to Your Task

Replace [sample-project/sample.py](sample-project/sample.py) with a safe task
of your own. Retain a mechanical success check and run Relay in every arm of a
comparison. Use the trace to identify behavior worth investigating before you
change a prompt, tool setup, model setting, or Hermes behavior.

Relay artifacts can contain prompts, tool output, file paths, and runtime
identifiers. Keep them local and review them before sharing.

## Troubleshooting

**Authentication fails:** Confirm that `NVIDIA_API_KEY` is set and can access
the model in [config/smoke.env](config/smoke.env).

**No ATOF or ATIF artifact appears:** Do not use `--safe-mode`, because it
disables custom Relay configuration. The runner prints the artifact directory
for each attempt.

**Hermes reaches its turn limit:** The runner marks this as a failed task. Read
the generated ATOF stream to determine whether the model, a tool, or the task
prompt caused the extra work.

## What You Learned

In this tutorial, you have:

- Enabled NeMo Relay for a local Hermes run without editing your normal Hermes
  profile.
- Verified a tool-use task and captured its ATOF and ATIF artifacts.
- Used Relay's summary to examine the model and tool activity behind an agent
  result.
- Established a trace-backed starting point for a controlled agent evaluation.

<details>
<summary>Run the repository checks</summary>

These checks use synthetic events and do not call a model or require an API
key.

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/render_relay_config.py scripts/summarize_atof.py
bash -n scripts/check_environment.sh scripts/run_tutorial.sh
```

</details>

## License

Apache-2.0. See [LICENSE](LICENSE).
