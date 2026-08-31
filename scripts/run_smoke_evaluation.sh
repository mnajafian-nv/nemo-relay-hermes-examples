#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
config_template="$repo_root/config/evaluation.plugins.toml"
smoke_config="$repo_root/config/smoke.env"

# shellcheck disable=SC1090
source "$smoke_config"

model="${MODEL:-$SMOKE_MODEL}"
runtime_root="${RUNTIME_ROOT:-/tmp/nemo-relay-hermes-examples}"
hermes_home="$runtime_root/hermes-home"
relay_output_root="$runtime_root/relay"
config_path="$runtime_root/evaluation.plugins.toml"

"$repo_root/scripts/check_environment.sh"
mkdir -p "$hermes_home" "$relay_output_root/atof" "$relay_output_root/atif"

python3 - "$config_template" "$config_path" "$relay_output_root" <<'PY'
from pathlib import Path
import sys

template_path, config_path, relay_output_root = map(Path, sys.argv[1:])
config = template_path.read_text(encoding="utf-8")
marker = "__RELAY_OUTPUT_ROOT__"
if marker not in config:
    raise SystemExit(f"Missing {marker} in {template_path}")
config_path.write_text(config.replace(marker, str(relay_output_root)), encoding="utf-8")
PY

set -a
source "$repo_root/keys.env"
set +a

export HERMES_HOME="$hermes_home"
export HERMES_NEMO_RELAY_PLUGINS_TOML="$config_path"
export NVIDIA_BASE_URL

cd "$repo_root/sample-project"

# This deterministic task verifies both the Hermes tool loop and Relay's local
# ATOF and ATIF projections. The output stays under /tmp, not in the repository.
hermes chat \
  --quiet \
  --provider nvidia \
  --model "$model" \
  --toolsets terminal \
  --query 'Use the terminal tool exactly once to run `python3 sample.py`. Then reply exactly with the command output. Do not inspect any other files.' \
  --max-turns "$SMOKE_MAX_TURNS" \
  --run-budget "$SMOKE_RUN_BUDGET_SECONDS" \
  --yolo \
  --ignore-user-config \
  --ignore-rules \
  | tee "$runtime_root/hermes-output.txt"

if rg -q 'No reply:|maximum tool-iteration' "$runtime_root/hermes-output.txt"; then
  echo "Hermes did not return a final response." >&2
  exit 1
fi
grep -Fq "$SMOKE_EXPECTED_OUTPUT" "$runtime_root/hermes-output.txt"
test -s "$relay_output_root/atof/run.jsonl"
find "$relay_output_root/atif" -type f -name '*.json' -size +0c -print -quit | grep -q .
