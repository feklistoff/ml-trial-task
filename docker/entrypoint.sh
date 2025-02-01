#!/bin/bash -l
set -e
if [ "$#" -eq 0 ]; then
  exec ml_trial_task -v docker_config.toml
else
  exec "$@"
fi
