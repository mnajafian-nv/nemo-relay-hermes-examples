#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

set -euo pipefail

repo_root="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
runtime_root="${TUTORIAL_RUNTIME_ROOT:-$repo_root/.tutorial-runtime}"
smoke_config="$repo_root/config/smoke.env"
uv_bin="$runtime_root/tools/uv"
hermes_source="$runtime_root/hermes-agent"
hermes_python="$runtime_root/venv/bin/python"
uv_installer=""

cleanup() {
  if [[ -n "$uv_installer" ]]; then
    rm -f -- "$uv_installer"
  fi
}

trap cleanup EXIT

if [[ ! -f "$smoke_config" ]]; then
  echo "Missing tutorial configuration: $smoke_config" >&2
  exit 1
fi

# shellcheck disable=SC1090
source "$smoke_config"

command -v git >/dev/null 2>&1 || {
  echo "Git is required to set up the tutorial runtime." >&2
  exit 1
}
command -v curl >/dev/null 2>&1 || {
  echo "curl is required to set up the tutorial runtime." >&2
  exit 1
}

mkdir -p "$runtime_root/tools"

if [[ ! -x "$uv_bin" ]]; then
  uv_installer="$(mktemp "${TMPDIR:-/tmp}/nemo-relay-hermes-uv.XXXXXX")"
  curl --fail --location --silent --show-error \
    https://astral.sh/uv/install.sh \
    --output "$uv_installer"
  UV_UNMANAGED_INSTALL="$runtime_root/tools" sh "$uv_installer"
fi

if [[ ! -d "$hermes_source/.git" ]]; then
  git init --quiet "$hermes_source"
  git -C "$hermes_source" remote add origin \
    https://github.com/NousResearch/hermes-agent.git
  git -C "$hermes_source" fetch --depth 1 origin "$HERMES_COMMIT"
  git -C "$hermes_source" checkout --quiet --detach FETCH_HEAD
elif [[ "$(git -C "$hermes_source" rev-parse HEAD)" != "$HERMES_COMMIT" ]]; then
  echo "Tutorial runtime is not pinned to $HERMES_REF ($HERMES_COMMIT)." >&2
  echo "Remove $runtime_root and run this script again." >&2
  exit 1
fi

export UV_CACHE_DIR="$runtime_root/cache"
export UV_MANAGED_PYTHON=1
export UV_PROJECT_ENVIRONMENT="$runtime_root/venv"
export UV_PYTHON_INSTALL_DIR="$runtime_root/python"
"$uv_bin" sync --project "$hermes_source" --locked --no-dev --python 3.11

if [[ ! -x "$hermes_python" ]]; then
  echo "Tutorial runtime did not create its Python environment." >&2
  exit 1
fi

installed_versions="$("$hermes_python" - <<'PY'
from importlib.metadata import version

from hermes_cli import __version__

print(f"{__version__} {version('nemo-relay')}")
PY
)"
read -r installed_hermes_version installed_relay_version <<<"$installed_versions"

if [[ "$installed_hermes_version" != "$HERMES_VERSION" ]]; then
  echo "Expected Hermes Agent $HERMES_VERSION, found $installed_hermes_version." >&2
  exit 1
fi
if [[ "$installed_relay_version" != "$NEMO_RELAY_VERSION" ]]; then
  echo "Expected nemo-relay $NEMO_RELAY_VERSION, found $installed_relay_version." >&2
  exit 1
fi

printf '%s\n' "Tutorial runtime is ready: Hermes $installed_hermes_version, nemo-relay $installed_relay_version."
