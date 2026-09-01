# Evaluation decision record

No result in this directory supports a public optimization claim.

| Work | Outcome | Decision |
| --- | --- | --- |
| Hermes + Relay smoke task | The task returned `VALUE=42` and Relay wrote ATOF and ATIF output. | Keep as the quickstart. It proves setup and trace capture only. |
| ToolPerf exploration | Both arms completed the selected tasks, or the candidate added work. | Do not report a performance result. |
| Output-recovery evaluator | A clean five-pair reproduction produced `0/5` trace-valid baseline recoveries and `2/5` candidate recoveries. | Keep as research only. Do not report a correctness, latency, cost, or quality result. |

The output-recovery fixture rejects runs that obtain the expected answer by
reading or inspecting the task artifact rather than retrieving the candidate's
spill file. That check exposed the failed reproduction and prevents a false
improvement claim.

A future case needs a mechanical verifier, trace evidence of a repeatable
baseline behavior, a narrowly related candidate, and a repeated alternating
result that reproduces from a clean checkout.
