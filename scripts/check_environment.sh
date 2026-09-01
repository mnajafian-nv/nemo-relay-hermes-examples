#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
smoke_config="$repo_root/config/smoke.env"
required_commands=(hermes)

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

if [[ -f "$repo_root/keys.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$repo_root/keys.env"
  set +a
fi

if [[ -z "${NVIDIA_API_KEY:-}" ]]; then
  echo "Set NVIDIA_API_KEY or copy keys.env.example to keys.env and set it there." >&2
  exit 1
fi

hermes_path="$(command -v hermes)"
hermes_python="${HERMES_PYTHON:-$(sed -n '1s/^#!//p' "$hermes_path")}"
if [[ ! -x "$hermes_python" ]]; then
  echo "Set HERMES_PYTHON to the Python interpreter used by Hermes." >&2
  exit 1
fi

hermes_version="$($hermes_python - <<'PY'
from hermes_cli import __version__

print(__version__)
PY
)"
if [[ "$hermes_version" != "$HERMES_VERSION" ]]; then
  echo "This tutorial was validated with Hermes Agent $HERMES_VERSION, found $hermes_version." >&2
  exit 1
fi

relay_version="$($hermes_python - <<'PY'
from importlib.metadata import PackageNotFoundError, version

try:
    print(version("nemo-relay"))
except PackageNotFoundError:
    print("not-installed")
PY
)"
if [[ "$relay_version" != "$NEMO_RELAY_VERSION" ]]; then
  echo "Hermes Agent $HERMES_VERSION must bundle nemo-relay $NEMO_RELAY_VERSION, found $relay_version." >&2
  exit 1
fi

printf '%s\n' "Environment is ready: Hermes $hermes_version, nemo-relay $NEMO_RELAY_VERSION."
