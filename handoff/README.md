# Shared tutorial handoff

This private lab is the source workspace. The shared repository should receive
only a tutorial that a reader can run without private checkouts, credentials, or
unpublished performance claims.

## Ready to transfer after alignment

- A minimal Relay plugin configuration.
- The deterministic smoke task and its verifier.
- A public-safe API-key template.
- A smoke runner that writes artifacts to a caller-selected directory.
- Setup, verification, and privacy guidance from the root README.
- The evaluation methodology, without private paths or historical figures.

## Keep private for now

- `evaluation/results.md`, which contains exploratory and historical results.
- `evaluation/manifest.yaml`, which records historical discovery work.
- `scripts/run_toolperf_ab.sh`, which depends on local pinned Hermes checkouts.
- Raw ATOF or ATIF artifacts, task outputs, logs, and credentials.

## Decisions needed before promotion

1. Which Hermes release and NVIDIA-hosted model the tutorial supports.
2. Whether the shared repository is the canonical tutorial location or only a
   staging repository for a later NVIDIA-owned location.
3. Whether the blog publishes trace setup and methodology only, or waits for a
   reproducible optimization result.
4. The exact baseline and candidate revisions for any published comparison.

## Publication gate

Promote an optimization result only when the candidate is independently
reproducible, completion does not regress, and repeated paired runs support the
specific claim. Report incomplete or mixed results as methodology, not as a
performance improvement.
