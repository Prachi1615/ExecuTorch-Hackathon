#!/bin/bash
# Start the robot. Extra flags are passed through, e.g.:
#   ./run.sh            normal demo (buttons, voice naming, servos)
#   ./run.sh --api      also serve the robot API for OM1
#   ./run.sh --api --no-mic   when OM1 is using the microphone
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/scripts/qnn_env.sh"
source "$HERE/.venv/bin/activate"
cd "$HERE"
python recognize.py watch "$@"
