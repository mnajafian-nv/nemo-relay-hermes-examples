# Evaluation results

## 2026-08-31: pinned ToolPerf discovery

**Question:** does the historical Hermes tool-layer candidate produce a
publishable improvement for `nvidia/nvidia/nemotron-3.5-lightning` on a
deterministic ToolPerf fixture?

### Current Hermes smoke check

The current Hermes checkout passed the deterministic smoke task with
`nvidia/qwen/qwen3.5-9b` on NVIDIA Inference. Hermes ran `python3 sample.py`,
returned `VALUE=42`, and Relay wrote both ATOF and ATIF artifacts.

The prior Lightning trial was not selected for the tutorial: it continued to
request additional terminal calls after receiving the correct result and reached
the turn limit. Relay still recorded those calls, but that is not a usable
quickstart contract.

**Decision:** use the Qwen configuration for the trace-capture walkthrough.
This passing smoke result validates setup only. It does not support a performance
claim.

### Historical ToolPerf environment

The remaining fields describe the earlier pinned ToolPerf comparison, not the
passing current-Hermes smoke task.

- Hermes baseline: `5b4d20b524` (`0.19.1`)
- Hermes candidate: `f01c193be4`
- NeMo Relay: `0.6.0`
- Model: `nvidia/nvidia/nemotron-3.5-lightning`
- Provider endpoint: `https://inference-api.nvidia.com/v1`
- Relay: ATOF enabled in the same isolated Hermes home for both arms
- Harness: ToolPerf `abeval`, `--max-turns 30`, 600-second per-run timeout

### `err_big_output`, 10 attempts per arm

| Arm | Verifier pass rate | Mean LLM calls | Mean tool calls | Mean wall time |
| --- | ---: | ---: | ---: | ---: |
| Baseline | 100% | 2.5 | 1.5 | 13s |
| Candidate | 100% | 2.6 | 1.6 | 13s |

**Decision:** do not use this as a performance headline. Both revisions solve
the task reliably and their aggregate execution cost is effectively the same.
The ATOF traces remain useful for demonstrating the setup and inspecting tool
and LLM lifecycle events.

### `err_python_env`, 3 attempts per arm

| Arm | Verifier pass rate | Mean LLM calls | Mean tool calls | Mean tool errors | Mean wall time |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 100% | 3.3 | 3.0 | 0.0 | 18s |
| Candidate | 100% | 4.3 | 4.3 | 0.3 | 16s |

**Decision:** do not use this fixture for the tutorial's improvement claim.
The selected model completes the task on both arms, and the candidate adds
agent activity rather than yielding a clear improvement.

## 2026-08-31: current-model selection run

**Question:** does the pinned ToolPerf candidate improve `err_big_output` for
the current smoke model?

**Environment:**

- Model: `nvidia/qwen/qwen3.5-9b`
- Provider endpoint: `https://inference-api.nvidia.com/v1`
- Harness: ToolPerf `abeval`, `err_big_output`, three attempts per arm
- Baseline: `5b4d20b524` (`0.19.1`)
- Candidate: `f01c193be4`
- Relay: ATOF enabled in both arms

| Arm | Verifier pass rate | Mean LLM calls | Mean tool calls | Mean tool errors | Mean retries | Mean wall time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 100% | 6.0 | 2.7 | 0.0 | 0.0 | 29s |
| Candidate | 100% | 9.0 | 4.7 | 0.3 | 0.3 | 32s |

**Decision:** do not use this candidate or fixture for the tutorial's
optimization claim. Completion is unchanged and the candidate adds execution
work. The retained traces are still useful for understanding the run shape, but
they do not justify a product-performance conclusion.

## 2026-08-31: isolated terminal-output retrieval trial

**Question:** when an oversized terminal response is recorded in a Relay trace,
does a narrow candidate that saves the complete response for later retrieval
reduce repeated agent work on `err_big_output`?

**Environment:**

- Model: `nvidia/qwen/qwen3.5-9b`
- Provider endpoint: `https://inference-api.nvidia.com/v1`
- Harness: ToolPerf `abeval`, `err_big_output`, five attempts per arm
- Baseline: `5b4d20b524` (`0.19.1`)
- Candidate: the output-truncation retrieval patch only, applied to the pinned
  baseline in a temporary worktree
- Relay: ATOF enabled in both arms

| Arm | Verifier pass rate | Mean LLM calls | Mean tool calls | Mean tool errors | Mean retries | Mean wall time |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Baseline | 100% | 6.0 | 2.6 | 0.0 | 0.0 | 19s |
| Candidate | 100% | 5.2 | 2.4 | 0.0 | 0.0 | 29s |

**Observation:** the candidate completed every run and reduced the observed LLM
and tool-call averages. It did not establish a latency improvement: one
81-second candidate run raises the five-run mean, and the benchmark executes
each arm in a batch rather than interleaving pairs.

**Decision:** this is trace-backed evidence that the candidate can reduce agent
activity on this fixture. It is not a publishable faster or lower-cost claim.
Any follow-up needs paired, interleaved repetitions and explicit token-cost
measurement before using this result outside the methodology section.

## Next selection gate

Before the tutorial claims that an evidence-backed Hermes change improved the
agent, a selected fixture must show all of the following:

1. A Relay trace identifies a repeatable baseline failure or inefficiency.
2. The candidate is narrowly tied to that behavior.
3. Repeated runs show a material verifier, latency, or cost improvement without
   a cross-model regression.

Until then, the tutorial should present Relay as the evidence layer for an
engineering decision, not as the source of an unverified performance claim.
