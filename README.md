# Trace a Hermes Task with NeMo Relay

Run a Hermes tool-use task through NVIDIA Inference, verify its deterministic
success condition, and inspect the NeMo Relay artifacts written to your machine.

The task asks Hermes to run `python3 sample.py`. The script prints `VALUE=42`,
so the task has one exact success condition and a trace that is small enough to
inspect.

## Prerequisites

Before you start, confirm the following:

- macOS or Linux
- Hermes Agent `0.20.5` or later
- Python 3.11 through 3.13 in the Python environment behind `hermes`
- An NVIDIA Inference API key with access to
  `nvidia/nvidia/nemotron-3.5-lightning`
- NeMo Relay `0.7.2` in Hermes's Python environment:

  ```bash
  HERMES_PYTHON="$(sed -n '1s/^#!//p' "$(command -v hermes)")"
  "$HERMES_PYTHON" -m pip install "nemo-relay==0.7.2"
  ```

Install Hermes with the [official installation guide](https://hermes-agent.nousresearch.com/docs/getting-started/installation). The model, Relay version, and execution limits are in [config/smoke.env](config/smoke.env).

## Run the Tutorial

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

   The runner creates an isolated Hermes home, renders a Relay `plugins.toml`,
   runs the task, and writes ATOF and ATIF artifacts under `artifacts/runs/` in
   the cloned repository. The retained directory contains task output and Relay
   artifacts, not Hermes authentication or runtime state. Set `RUNTIME_ROOT`
   to store artifacts in a different user-owned location.

**Expected result:** The command prints `Task verified: VALUE=42`, a trace
summary with at least one completed LLM scope and tool call, `tool errors: 0`,
and the artifact directory.

## Inspect the Relay Artifacts

The runner prints a summary automatically. Run the summarizer again by using
the artifact directory from the previous step:

```bash
HERMES_PYTHON="$(sed -n '1s/^#!//p' "$(command -v hermes)")"
"$HERMES_PYTHON" scripts/summarize_atof.py \
  <artifact-directory>/atof/run.jsonl
```

| Question | Where to look |
| --- | --- |
| Did the task finish? | `VALUE=42` and a completed ATIF trajectory. |
| Which model and tool calls ran? | The printed summary and ATOF event stream. |
| Did a tool fail? | `tool errors` and the raw ATOF events. |

ATOF is Relay's ordered event stream. ATIF is the agent trajectory Relay
derives from lifecycle events. Review artifacts before sharing them. They can
contain prompts, tool arguments and results, file paths, model output, and
other application data.

## Apply the Pattern to Your Task

Replace [sample-project/sample.py](sample-project/sample.py) with a safe task
of your own. Keep a mechanical success check, capture Relay artifacts for each
run, and compare equivalent runs before and after a focused agent change.

## Troubleshooting

**Authentication fails:** Confirm that `NVIDIA_API_KEY` is set and can access
the model in [config/smoke.env](config/smoke.env).

**No ATOF or ATIF artifact appears:** Do not use `--safe-mode`, because it
disables custom Relay configuration. When a run creates artifacts, the runner
prints their directory even if the task later fails.

**Hermes reaches its turn limit:** The runner marks the task as failed. Use the
ATOF stream to identify whether the model, tool, or task prompt caused the
extra work.

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
