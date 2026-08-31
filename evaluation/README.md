# Evaluation plan

Use this path only after the quickstart smoke task works.

## Question

Can a Relay trace explain a concrete Hermes tool-use behavior, and can the same deterministic fixture evaluate a pinned baseline and candidate revision?

## Candidate selection

The public [Hermes ToolPerf suite](https://github.com/NousResearch/hermes-toolperf-evals)
provides deterministic fixtures and a Relay ATOF-scored baseline/candidate
harness. It is the starting point for this tutorial's evaluation path, not a
source of a preselected headline.

Choose a fixture only after its trace demonstrates the behavior that a narrowly
scoped Hermes change is intended to address. The final case must have a
mechanical verifier, a traceable baseline failure or repeated inefficiency, and
a candidate that targets that behavior.

The smoke task and this fixture serve different purposes:

- The smoke task verifies installation and local Relay output.
- The ToolPerf fixture supplies a controlled trace and A/B evaluation path.

## Protocol

1. Revalidate the smoke task and selected fixture against the Hermes release
   used by the tutorial.
2. Capture and annotate a baseline trace that shows the target behavior. Do not
   infer a failure pattern from a successful result alone.
3. Freeze the model identifier, provider settings, timeout, maximum turns,
   Relay configuration, task fixture, source revisions, and evaluation date.
4. Run the selected fixture against the pinned baseline and candidate with at
   least three attempts per arm. Increase the sample when the observed delta is
   small or variable.
5. Report the verifier pass rate as the primary metric. Report wall time, LLM
   turns, tool calls, retries, and result bytes as secondary metrics.

## Reporting rules

- Keep Relay enabled in both arms. It is the evidence source, not the treatment.
- State the model identifier, provider endpoint, and execution date with every result.
- Publish aggregate results only. Do not publish raw prompts, raw tool output, telemetry payloads, or credentials.
- If the validation result is inconclusive, publish the method and limitation rather than claiming improvement.
- Label historical ToolPerf results as historical. Do not present them as a new NVIDIA benchmark result.

## Local runner

`../scripts/run_toolperf_ab.sh` runs one fixture through two pinned Hermes
trees with Relay ATOF enabled in an isolated Hermes home. It never writes
credentials, traces, or task artifacts into this repository. Set
`TOOLPERF_DIR`, `BASELINE_TREE`, and `CANDIDATE_TREE` to the corresponding local
checkouts. The script prints the aggregate table and leaves the raw artifacts
under `/tmp` for review.

See [results.md](results.md) for completed experiments and publication
decisions.
