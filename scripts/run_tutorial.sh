#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_root="${RUNTIME_ROOT:-$repo_root/artifacts}"
run_root="$runtime_root/runs/$(date -u +%Y%m%dT%H%M%SZ)-$$"
hermes_home="$(mktemp -d "${TMPDIR:-/tmp}/nemo-relay-hermes-tutorial.XXXXXX")"
plugins_path="$hermes_home/plugins.toml"
trace_path="$run_root/atof/run.jsonl"
run_succeeded=false

cleanup_hermes_home() {
  rm -rf -- "$hermes_home"
  if [[ "$run_succeeded" != true && -d "$run_root" ]]; then
    printf '\nArtifacts: %s\n' "$run_root" >&2
  fi
}

trap cleanup_hermes_home EXIT
trap 'exit 130' INT
trap 'exit 143' TERM HUP

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
docker_image="$SMOKE_DOCKER_IMAGE"
terminal_cwd="$SMOKE_TERMINAL_CWD"

command -v docker >/dev/null || {
  echo "Docker is required because this tutorial runs terminal commands in an isolated container." >&2
  exit 1
}
docker image inspect "$docker_image" >/dev/null 2>&1 || {
  echo "Tutorial image $docker_image is not available. Run ./scripts/build_tutorial_image.sh first." >&2
  exit 1
}

mkdir -p "$run_root"
"$hermes_python" "$repo_root/scripts/render_relay_config.py" \
  --output "$plugins_path" \
  --output-directory "$run_root" \
  --model-name "$model" >/dev/null

export HERMES_HOME="$hermes_home"
export HERMES_NEMO_RELAY_PLUGINS_TOML="$plugins_path"
export NVIDIA_BASE_URL
# The tutorial task is intentionally fixed and runs in an ephemeral container.
# Do not fall back to Hermes' host-terminal default when the caller has a
# conflicting terminal environment in their shell.
export TERMINAL_ENV=docker
export TERMINAL_DOCKER_IMAGE="$docker_image"
export TERMINAL_CWD="$terminal_cwd"
export TERMINAL_CONTAINER_PERSISTENT=false
export TERMINAL_DOCKER_NETWORK=false
export TERMINAL_DOCKER_EXTRA_ARGS='["--read-only", "--tmpfs", "/tmp:rw,exec,size=1g"]'

# Keep the task prompt and success check in the public smoke contract so a
# reader can adapt the fixture without editing the runner.
query="$SMOKE_QUERY"
output_path="$run_root/hermes-output.txt"

(
  cd "$repo_root/sample-project"
  "$hermes_python" -m hermes_cli.main chat \
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
trajectory_path="$(find "$run_root/atif" -type f -name 'trajectory-*.json' -size +0c -print -quit)"
test -n "$trajectory_path"

printf 'ATOF summary:\n'
"$hermes_python" "$repo_root/scripts/summarize_atof.py" \
  "$trace_path" \
  --require-completed-llm-scope \
  --require-tool-call \
  --require-no-tool-errors \
  --require-tool-command "$SMOKE_REQUIRED_TOOL_COMMAND"
printf '\nATIF summary:\n'
"$hermes_python" "$repo_root/scripts/summarize_atif.py" "$trajectory_path"
run_succeeded=true
printf '\nTask verified: %s\n' "$SMOKE_EXPECTED_OUTPUT"
printf '\nArtifacts: %s\n' "$run_root"
