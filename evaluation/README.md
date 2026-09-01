# Experimental evaluation

This directory is not part of the quickstart. It holds exploratory tools for
developing a trace-backed Hermes improvement case. It does not contain a
publishable benchmark result.

## Current status

The output-recovery evaluator compares two pinned Hermes revisions. A run is
accepted only when the final response is correct and the Relay trace proves the
candidate recovered terminal output through its spill artifact.

The first clean reproduction produced `0/5` trace-valid recoveries for the
baseline and `2/5` for the candidate. The candidate result was not repeatable,
so do not use this evaluator to claim a correctness, latency, cost, or model
quality improvement. The short decision record is in [results.md](results.md).

## Using the evaluator

Use this only when developing a future experiment. You need local worktrees for
the pinned Hermes baseline and candidate, a compatible Python environment, and
an NVIDIA Inference API key in `keys.env` at the repository root.

```bash
python3 evaluation/run_output_recovery_case.py --help
```

The runner writes traces and result artifacts under `artifacts/` in the cloned
repository by default. This directory is ignored by Git. Keep those artifacts
local because they can contain prompts, tool output, paths, and runtime
identifiers.

## Evidence standard for a future comparison

Before describing an improvement publicly, require all of the following:

1. A Relay trace identifies a repeatable baseline behavior.
2. The candidate is narrowly tied to that behavior.
3. The fixture mechanically verifies the intended behavior.
4. Repeated, alternating runs reproduce a material result without a
   cross-model regression.

Relay stays enabled in both arms. It supplies the evidence; the Hermes change
is the treatment.
