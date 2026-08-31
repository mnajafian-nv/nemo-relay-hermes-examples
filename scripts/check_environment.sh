#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
smoke_config="$repo_root/config/smoke.env"
required_commands=(hermes python3)

if [[ ! -f "$smoke_config" ]]; then
  echo "Missing smoke configuration: $smoke_config" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$smoke_config"

for command in "${required_commands[@]}"; do
  if ! command -v "$command" >/dev/null 2>&1; then
    echo "Missing required command: $command" >&2
    exit 1
  fi
done

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

hermes_version_output="$(hermes --version 2>&1)"
if ! grep -Fq "Hermes Agent v$HERMES_AGENT_VERSION" <<<"$hermes_version_output"; then
  echo "Expected Hermes Agent $HERMES_AGENT_VERSION." >&2
  echo "$hermes_version_output" >&2
  exit 1
fi

hermes_path="$(command -v hermes)"
hermes_python="${HERMES_PYTHON:-$(sed -n '1s/^#!//p' "$hermes_path")}"
if [[ ! -x "$hermes_python" ]]; then
  echo "Set HERMES_PYTHON to the Python interpreter used by Hermes." >&2
  exit 1
fi

relay_version="$($hermes_python - <<'PY'
from importlib.metadata import PackageNotFoundError, version

try:
    print(version("nemo-relay"))
except PackageNotFoundError:
    raise SystemExit("not-installed")
PY
)"
if [[ "$relay_version" != "$NEMO_RELAY_VERSION" ]]; then
  echo "Expected nemo-relay $NEMO_RELAY_VERSION, found $relay_version." >&2
  exit 1
fi

echo "Environment is ready: Hermes $HERMES_AGENT_VERSION, nemo-relay $NEMO_RELAY_VERSION."
