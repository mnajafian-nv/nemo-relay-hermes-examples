#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_root="${RUNTIME_ROOT:-/tmp/nemo-relay-hermes-examples}"
run_root="$runtime_root/runs/$(date -u +%Y%m%dT%H%M%SZ)-$$"
hermes_home="$run_root/hermes-home"
plugins_path="$hermes_home/plugins.toml"
trace_path="$hermes_home/atof/run.jsonl"

if [[ -f "$repo_root/keys.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$repo_root/keys.env"
  set +a
fi

"$repo_root/scripts/check_environment.sh"
hermes_path="$(command -v hermes)"
hermes_python="${HERMES_PYTHON:-$(sed -n '1s/^#!//p' "$hermes_path")}"

# shellcheck disable=SC1090
source "$repo_root/config/smoke.env"
model="${MODEL:-$SMOKE_MODEL}"
mkdir -p "$hermes_home"
"$hermes_python" "$repo_root/scripts/render_relay_config.py" \
  --output "$plugins_path" \
  --output-directory "$hermes_home" \
  --model-name "$model" >/dev/null

export HERMES_HOME="$hermes_home"
export HERMES_NEMO_RELAY_PLUGINS_TOML="$plugins_path"
export NVIDIA_BASE_URL

query='Run exactly `python3 sample.py` in the current directory. Reply with only the exact output line.'
output_path="$run_root/hermes-output.txt"
mkdir -p "$run_root"

(
  cd "$repo_root/sample-project"
  hermes chat \
    --provider nvidia \
    --model "$model" \
    --toolsets terminal \
    --query "$query" \
    --max-turns "$SMOKE_MAX_TURNS" \
    --run-budget "$SMOKE_RUN_BUDGET_SECONDS" \
    --accept-hooks \
    --quiet
) | tee "$output_path"

if grep -Eq 'No reply:|maximum tool-iteration' "$output_path"; then
  echo "Hermes did not return a final response." >&2
  exit 1
fi
grep -qxF "$SMOKE_EXPECTED_OUTPUT" "$output_path"
test -s "$trace_path"
find "$hermes_home/atif" -type f -name 'trajectory-*.json' -size +0c -print -quit | grep -q .

printf '\nTask verified: %s\n' "$SMOKE_EXPECTED_OUTPUT"
printf 'Trace summary:\n'
"$hermes_python" "$repo_root/scripts/summarize_atof.py" "$trace_path"
printf '\nArtifacts: %s\n' "$run_root"
