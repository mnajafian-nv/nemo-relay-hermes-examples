#!/usr/bin/env bash
set -euo pipefail

# Run one deterministic Hermes ToolPerf fixture through pinned baseline and
# candidate source trees. Relay is enabled in an isolated Hermes home for both
# arms, and raw artifacts stay in the repository's ignored artifacts directory
# by default.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
toolperf_dir="${TOOLPERF_DIR:?Set TOOLPERF_DIR to the ToolPerf harness directory.}"
baseline_tree="${BASELINE_TREE:?Set BASELINE_TREE to the pinned Hermes baseline tree.}"
candidate_tree="${CANDIDATE_TREE:?Set CANDIDATE_TREE to the pinned Hermes candidate tree.}"
model="${MODEL:-nvidia/nvidia/nemotron-3.5-lightning}"
task="${TASK:-err_big_output}"
repetitions="${REPETITIONS:-3}"
evaluation_root="${EVALUATION_ROOT:-$repo_root/artifacts/toolperf/run}"
python="${PYTHON:-$baseline_tree/.venv/bin/python}"

if [[ ! "$repetitions" =~ ^[1-9][0-9]*$ ]]; then
  echo "REPETITIONS must be a positive integer, found: $repetitions" >&2
  exit 1
fi

if [[ -f "$toolperf_dir/abeval/ab_eval.py" ]]; then
  evaluator="$toolperf_dir/abeval/ab_eval.py"
elif [[ -f "$toolperf_dir/ab_eval.py" ]]; then
  evaluator="$toolperf_dir/ab_eval.py"
else
  echo "Could not find ab_eval.py beneath TOOLPERF_DIR: $toolperf_dir" >&2
  exit 1
fi

for path in "$baseline_tree" "$candidate_tree"; do
  if [[ ! -e "$path" ]]; then
    echo "Required path does not exist: $path" >&2
    exit 1
  fi
done

if [[ ! -x "$python" ]]; then
  echo "Missing evaluation Python: $python" >&2
  echo "Create the baseline environment from its pinned lockfile first." >&2
  exit 1
fi

if [[ ! -f "$repo_root/keys.env" ]]; then
  echo "Missing keys.env. Copy keys.env.example and set NVIDIA_API_KEY." >&2
  exit 1
fi

set -a
source "$repo_root/keys.env"
set +a

if [[ -z "${NVIDIA_API_KEY:-}" ]]; then
  echo "NVIDIA_API_KEY is empty in keys.env." >&2
  exit 1
fi

export NVIDIA_BASE_URL="${NVIDIA_BASE_URL:-https://inference-api.nvidia.com/v1}"
export ABEVAL_ROOT="$evaluation_root"
export ABEVAL_HOME="$evaluation_root/home"

mkdir -p "$ABEVAL_ROOT"

# The Hermes Relay plugin is opt-in. The per-run plugins.toml configures its
# exporters after discovery, but does not enable plugin discovery itself.
# Keep this state in the evaluation-only home so the run cannot mutate a
# developer's normal Hermes profile.
HERMES_HOME="$ABEVAL_HOME" PYTHONPATH="$baseline_tree" \
  "$python" -m hermes_cli.main plugins enable observability/nemo_relay

# The evaluator is resume-safe: asking for N repetitions runs only missing
# records through r(N-1). Alternate the arms so transient provider or host
# variation is not confounded with the candidate revision.
for ((pair = 1; pair <= repetitions; pair += 1)); do
  if (( pair % 2 )); then
    "$python" "$evaluator" run \
      --arm baseline --model "$model" --reps "$pair" \
      --pythonpath "$baseline_tree" --only "$task"
    "$python" "$evaluator" run \
      --arm fixes --model "$model" --reps "$pair" \
      --pythonpath "$candidate_tree" --only "$task"
  else
    "$python" "$evaluator" run \
      --arm fixes --model "$model" --reps "$pair" \
      --pythonpath "$candidate_tree" --only "$task"
    "$python" "$evaluator" run \
      --arm baseline --model "$model" --reps "$pair" \
      --pythonpath "$baseline_tree" --only "$task"
  fi
done
"$python" "$evaluator" report --models "$model"
