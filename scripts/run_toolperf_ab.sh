#!/usr/bin/env bash
set -euo pipefail

# Run one deterministic Hermes ToolPerf fixture through pinned baseline and
# candidate source trees. Relay is enabled in an isolated Hermes home for both
# arms, and all raw artifacts stay beneath /tmp by default.

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
toolperf_dir="${TOOLPERF_DIR:?Set TOOLPERF_DIR to hermes-toolperf-evals.}"
baseline_tree="${BASELINE_TREE:?Set BASELINE_TREE to the pinned Hermes baseline tree.}"
candidate_tree="${CANDIDATE_TREE:?Set CANDIDATE_TREE to the pinned Hermes candidate tree.}"
model="${MODEL:-nvidia/nvidia/nemotron-3.5-lightning}"
task="${TASK:-err_big_output}"
repetitions="${REPETITIONS:-3}"
evaluation_root="${EVALUATION_ROOT:-/tmp/nemo-relay-hermes-examples/toolperf/run}"
python="${PYTHON:-$baseline_tree/.venv/bin/python}"

for path in "$toolperf_dir/abeval/ab_eval.py" "$baseline_tree" "$candidate_tree"; do
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
HERMES_HOME="$ABEVAL_HOME" PYTHONPATH="$baseline_tree" \
  "$python" -m hermes_cli.main plugins enable observability/nemo_relay

"$python" "$toolperf_dir/abeval/ab_eval.py" run \
  --arm baseline --model "$model" --reps "$repetitions" \
  --pythonpath "$baseline_tree" --only "$task"
"$python" "$toolperf_dir/abeval/ab_eval.py" run \
  --arm fixes --model "$model" --reps "$repetitions" \
  --pythonpath "$candidate_tree" --only "$task"
"$python" "$toolperf_dir/abeval/ab_eval.py" report --models "$model"
