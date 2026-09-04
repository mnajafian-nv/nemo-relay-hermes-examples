#!/usr/bin/env bash
set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_root="${TUTORIAL_RUNTIME_ROOT:-$repo_root/.tutorial-runtime}"
smoke_config="$repo_root/config/smoke.env"

if [[ ! -f "$smoke_config" ]]; then
  echo "Missing smoke configuration: $smoke_config" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$smoke_config"

if [[ -z "${NVIDIA_API_KEY:-}" && -f "$repo_root/keys.env" ]]; then
  set -a
  # shellcheck disable=SC1090
  source "$repo_root/keys.env"
  set +a
fi

if [[ -z "${NVIDIA_API_KEY:-}" ]]; then
  echo "Set NVIDIA_API_KEY or copy keys.env.example to keys.env and set it there." >&2
  exit 1
fi

hermes_python="$runtime_root/venv/bin/python"
if [[ ! -x "$hermes_python" ]]; then
  echo "Tutorial runtime is unavailable. Run ./scripts/setup_tutorial_runtime.sh first." >&2
  exit 1
fi

hermes_version="$($hermes_python - <<'PY'
from hermes_cli import __version__

print(__version__)
PY
)"

relay_version="$($hermes_python - <<'PY'
from importlib.metadata import PackageNotFoundError, version

try:
    print(version("nemo-relay"))
except PackageNotFoundError:
    print("not-installed")
PY
)"
if [[ "$relay_version" != "$NEMO_RELAY_VERSION" ]]; then
  echo "Hermes Agent must bundle nemo-relay $NEMO_RELAY_VERSION, found $relay_version." >&2
  exit 1
fi

if [[ "$hermes_version" != "$HERMES_VERSION" ]]; then
  echo "Tutorial runtime must use Hermes Agent $HERMES_VERSION, found $hermes_version." >&2
  exit 1
fi

printf '%s\n' "Environment is ready: Hermes $hermes_version, nemo-relay $NEMO_RELAY_VERSION."
