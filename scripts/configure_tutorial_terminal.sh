#!/usr/bin/env bash
# SPDX-FileCopyrightText: Copyright (c) 2026, NVIDIA CORPORATION & AFFILIATES. All rights reserved.
# SPDX-License-Identifier: Apache-2.0

# Configure the terminal backend used by the tutorial. This script deliberately
# overwrites inherited Docker settings so an existing Hermes shell profile cannot
# add mounts, inject environment variables, or weaken the container boundary.

configure_tutorial_terminal() {
  local image="$1"
  local cwd="$2"

  export TERMINAL_ENV=docker
  export TERMINAL_DOCKER_IMAGE="$image"
  export TERMINAL_CWD="$cwd"
  export TERMINAL_CONTAINER_PERSISTENT=false
  export TERMINAL_DOCKER_NETWORK=false
  export TERMINAL_DOCKER_VOLUMES='[]'
  export TERMINAL_DOCKER_FORWARD_ENV='[]'
  export TERMINAL_DOCKER_ENV='{}'
  export TERMINAL_DOCKER_MOUNT_CWD_TO_WORKSPACE=false
  export TERMINAL_DOCKER_RUN_AS_HOST_USER=false
  export TERMINAL_DOCKER_PERSIST_ACROSS_PROCESSES=false
  export TERMINAL_DOCKER_EXTRA_ARGS='["--read-only", "--tmpfs", "/tmp:rw,exec,size=1g"]'
}
