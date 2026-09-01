# Hermes and NeMo Relay example

Run a small Hermes tool-use task through NVIDIA Inference, verify its result,
and inspect the NeMo Relay trace produced locally.

This is a runnable observability walkthrough. It shows what happened during an
agent run. It does not claim that Relay alone improves quality, latency, or
cost.

## What you will do

The tutorial asks Hermes to run `python3 sample.py` and return its output.
The runner then verifies `VALUE=42`, confirms that Relay wrote ATOF and ATIF
artifacts, and prints a compact ATOF summary.

The result gives you evidence for four basic questions:

| Question | Evidence |
| --- | --- |
| Did the task finish? | `VALUE=42` and a completed ATIF file. |
| Did Relay capture the run? | A non-empty ATOF JSONL file. |
| Did Hermes call a model and a tool? | Completed LLM scopes and tool calls in the summary. |
| Where are the artifacts? | The final line printed by the runner. |

## Prerequisites

- macOS or Linux
- Hermes Agent `0.20.5` or later
- Python 3.11 or later in the Python environment used by `hermes`
- NeMo Relay `0.7.2` installed in that same environment
- An NVIDIA Inference API key with access to
  `nvidia/nvidia/nemotron-3.5-lightning`

The version and model are the verified tutorial contract in
[config/smoke.env](config/smoke.env). Hermes owns Relay natively in this
release. Do not enable the removed `observability/nemo_relay` Hermes plugin.

Install Hermes using the [official guide](https://hermes-agent.nousresearch.com/docs/getting-started/installation), then install Relay into Hermes's Python environment:

```bash
HERMES_PYTHON="$(sed -n '1s/^#!//p' "$(command -v hermes)")"
"$HERMES_PYTHON" -m pip install "nemo-relay==0.7.2"
```

## Run the tutorial

Clone the repository, export your NVIDIA key, and run one command:

```bash
git clone https://github.com/mnajafian-nv/nemo-relay-hermes-examples.git
cd nemo-relay-hermes-examples
export NVIDIA_API_KEY="<your NVIDIA Inference API key>"
./scripts/run_tutorial.sh
```

The runner creates an isolated Hermes profile for each run and prints the
artifact directory when it finishes. It writes below
`/tmp/nemo-relay-hermes-examples` by default. Set `RUNTIME_ROOT` to use a
different local directory.

If you prefer not to export a key in your shell, copy
[keys.env.example](keys.env.example) to `keys.env` and set `NVIDIA_API_KEY`
there. `keys.env` is ignored by Git.

## Read the trace

The runner prints a summary automatically. To repeat it later:

```bash
HERMES_PYTHON="$(sed -n '1s/^#!//p' "$(command -v hermes)")"
"$HERMES_PYTHON" scripts/summarize_atof.py \
  <artifact-directory>/hermes-home/atof/run.jsonl
```

ATOF is Relay's event stream. ATIF is the completed agent trajectory assembled
from that stream. Both can contain prompts, tool arguments, tool output, local
paths, and runtime identifiers. Treat them as sensitive and sanitize them
before sharing. Do not commit generated traces or logs.

## Use this pattern on your task

Replace [sample-project/sample.py](sample-project/sample.py) with a safe task
and retain a mechanical success check. Run the task with Relay enabled in every
comparison. The trace identifies the behavior to investigate; a controlled
change to Hermes, the prompt, tools, or model settings is what can change the
result.

[evaluation/](evaluation/) records the evidence standard for a future
before-and-after case study. It deliberately does not publish a performance
claim from the exploratory work currently in this repository.

## Development checks

The synthetic checks do not call a model or require an API key:

```bash
python3 -m unittest discover -s tests -v
python3 -m py_compile scripts/render_relay_config.py scripts/summarize_atof.py
bash -n scripts/check_environment.sh scripts/run_tutorial.sh
```
