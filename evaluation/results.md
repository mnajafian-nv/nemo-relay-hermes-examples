# Evaluation results

## 2026-08-31: pinned ToolPerf discovery

**Question:** does the historical Hermes tool-layer candidate produce a
publishable improvement for `nvidia/nvidia/nemotron-3.5-lightning` on a
deterministic ToolPerf fixture?

### Current Hermes smoke check

The current Hermes checkout passed the deterministic smoke task with
`nvidia/nvidia/nemotron-3.5-lightning` on NVIDIA Inference. Hermes ran
`python3 sample.py`, returned `VALUE=42`, and Relay wrote both ATOF and ATIF
artifacts.

**Decision:** use this Nemotron configuration for the trace-capture walkthrough.
This passing smoke result validates setup only. It does not support a
performance claim.

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

**Decision:** reject this as decision evidence. The fixture places the expected
token directly in readable Python source, so the verifier does not require the
agent to recover it from truncated terminal output. The benchmark also ran each
arm as a batch. The observed call-count difference is therefore not evidence
that the output-retrieval candidate improved the intended behavior.

## 2026-08-31: unconstrained output-retrieval check

**Question:** does the upstream output-retrieval candidate improve a traced,
alternating comparison on `err_big_output` with the NVIDIA-hosted Nemotron
configuration?

**Environment:**

- Model: `nvidia/nvidia/nemotron-3.5-lightning`
- Provider endpoint: `https://inference-api.nvidia.com/v1`
- Harness: ToolPerf `abeval`, `err_big_output`, five alternating pairs
- Baseline: `1c6d1a23c081014ce70595396c4becc1112426b8`
- Candidate: `80631c4aeaa34e4c0f3aca987992846593c333b1`
- Relay: ATOF enabled in the same isolated Hermes home for both arms

| Arm | Verifier pass rate | Mean LLM calls | Mean tool calls | Mean result bytes | Mean wall time |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 100% | 3.0 | 2.0 | 10 KB | 12s |
| Candidate | 100% | 3.4 | 2.4 | 31 KB | 14s |

**Trace check:** all ten runs wrote ATOF artifacts. The candidate emitted
spill-file metadata when its terminal output overflowed, so the intended code
path was exercised.

**Decision:** reject this fixture as the blog optimization case. Both arms
solve it, and the candidate adds work. More importantly, `noisy_build.py`
contains the token in readable source, so a model can answer without recovering
the omitted terminal output. The result is useful for validating trace capture
and rejecting a weak benchmark, not for claiming an agent improvement.

## 2026-08-31: trace-validated output-recovery case

**Question:** can the output-retrieval candidate recover a token that exists
only in oversized terminal output, where the trace proves the recovery path?

**Environment:**

- Model: `nvidia/nvidia/nemotron-3.5-lightning`
- Provider endpoint: `https://inference-api.nvidia.com/v1`
- Harness: focused output-recovery fixture, five alternating pairs
- Baseline: `1c6d1a23c081014ce70595396c4becc1112426b8`
- Candidate: `80631c4aeaa34e4c0f3aca987992846593c333b1`
- Relay: ATOF enabled in the same isolated Hermes home for both arms

The fixture deletes its readable source as it begins execution. A run passes
only if the final response contains the token and its Relay trace shows exactly
one execution of the fixture followed by `search_files` or `read_file` on the
candidate spill artifact. This rejects source inspection, output filtering, and
rerunning the command as substitutes for recovery.

| Arm | Trace-valid recovery | Mean LLM calls | Mean tool calls | Mean result bytes | Mean wall time |
| --- | ---: | ---: | ---: | ---: | ---: |
| Baseline | 0/5 | 1.0 | 0.8 | 15 KB | 88s |
| Candidate | 5/5 | 3.0 | 2.0 | 50 KB | 13s |

**Decision:** use this as the blog's focused recovery case study. It proves a
correctness and wall-time improvement for the intended failure mode. It does
not establish a general agent benchmark or a cost reduction: the successful
candidate performs an extra retrieval step and produces larger tool results.

## Next selection gate

Before the tutorial claims that an evidence-backed Hermes change improved the
agent, a selected fixture must show all of the following:

1. A Relay trace identifies a repeatable baseline failure or inefficiency.
2. The candidate is narrowly tied to that behavior.
3. The fixture requires the intended recovery behavior rather than exposing the
   expected answer in readable task source.
4. Repeated, alternating runs show a material verifier, latency, or cost
   improvement without a cross-model regression.

Until then, the tutorial should present Relay as the evidence layer for an
engineering decision, not as the source of an unverified performance claim.
