# Trace a Hermes task with NeMo Relay

Run one small Hermes task through NVIDIA Inference, verify the result, and read
the NeMo Relay trace it creates on your machine.

This walkthrough gives you a working baseline for tracing a tool-using agent.
It does not claim that Relay alone improves agent quality, latency, or cost.

## What you will learn

By the end, you will have:

1. run Hermes with NeMo Relay enabled;
2. verified a tool-use task mechanically;
3. captured ATOF events and an ATIF trajectory locally; and
4. used the summary to see model calls, tool calls, and tool failures.

The tutorial uses a deterministic program that prints `VALUE=42`. It keeps the
task small so the result is clear and the trace is easy to inspect.

## Before you begin

| Requirement | Verified tutorial contract |
| --- | --- |
| Operating system | macOS or Linux |
| Hermes Agent | `0.20.5` or later |
| Python | 3.11 or later in Hermes's environment |
| NeMo Relay | `0.7.2` in that same environment |
| Provider | NVIDIA Inference |
| Model | `nvidia/nvidia/nemotron-3.5-lightning` |

The exact values live in [config/smoke.env](config/smoke.env). Hermes owns the
Relay runtime in this release. Do not enable the removed
`observability/nemo_relay` Hermes plugin.

Install Hermes with the [official guide](https://hermes-agent.nousresearch.com/docs/getting-started/installation), then install Relay into the Python environment behind the `hermes` command:

```bash
HERMES_PYTHON="$(sed -n '1s/^#!//p' "$(command -v hermes)")"
"$HERMES_PYTHON" -m pip install "nemo-relay==0.7.2"
```

## 1. Run the tutorial

Clone the repository, provide an NVIDIA Inference key, then run the tutorial:

```bash
git clone https://github.com/mnajafian-nv/nemo-relay-hermes-examples.git
cd nemo-relay-hermes-examples
export NVIDIA_API_KEY="<your NVIDIA Inference API key>"
./scripts/run_tutorial.sh
```

The runner creates an isolated Hermes profile for every run. It renders the
Relay configuration, runs the task, verifies the final answer, checks for both
ATOF and ATIF output, and prints the trace summary. You do not need to edit a
Hermes profile or write a `plugins.toml` manually.

If you prefer not to export a key in your shell, copy
[keys.env.example](keys.env.example) to `keys.env` and set `NVIDIA_API_KEY`
there. `keys.env` is ignored by Git.

## 2. Check the result

A successful run ends with output like this:

```text
Task verified: VALUE=42
Trace summary:
completed llm scopes: <count>
tool calls: <count>
tool errors: 0
Artifacts: <local directory>
```

The exact counts depend on the model's tool-use decisions. The portable
contract is the verified final answer, a non-empty ATOF JSONL file, and a
completed ATIF trajectory.

## 3. Read the trace

The runner prints a summary automatically. To inspect the same trace later,
copy the `Artifacts:` directory from its output:

```bash
HERMES_PYTHON="$(sed -n '1s/^#!//p' "$(command -v hermes)")"
"$HERMES_PYTHON" scripts/summarize_atof.py \
  <artifact-directory>/hermes-home/atof/run.jsonl
```

| Question | Trace evidence |
| --- | --- |
| Did the task finish? | `VALUE=42` and a completed ATIF file. |
| Did Hermes use a model? | `completed llm scopes` is nonzero. |
| Did Hermes use a tool? | `tool calls` is nonzero. |
| Did a tool report failure? | Review `tool errors` and the raw ATOF events. |

ATOF is Relay's event stream. ATIF is the completed agent trajectory assembled
from that stream. Both can contain prompts, tool arguments, tool output, local
paths, and runtime identifiers. Treat generated artifacts as sensitive and
sanitize them before sharing.

## Apply it to your task

Replace [sample-project/sample.py](sample-project/sample.py) with a safe task
of your own and keep a mechanical success check. Run Relay in every comparison.
Use the trace to find behavior worth investigating, then test a controlled
change to Hermes, the prompt, tools, or model settings.

The exploratory material in [evaluation/](evaluation/) documents the evidence
standard for a future before-and-after case study. It does not support a public
performance claim today.

## Troubleshooting

**Authentication fails:** confirm `NVIDIA_API_KEY` is set and has access to the
model in [config/smoke.env](config/smoke.env).

**No ATOF or ATIF artifact appears:** rerun without `--safe-mode`, which
disables custom Relay configuration. The runner prints the artifact directory
for the failing run.

**Hermes reaches its turn limit:** the runner treats this as a failed task.
Read the generated ATOF stream to determine whether the model, a tool, or the
task prompt caused the extra work.

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
