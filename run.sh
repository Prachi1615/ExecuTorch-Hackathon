#!/bin/bash
# Start the robot. Extra flags are passed through, e.g.:
#   ./run.sh               normal demo (buttons, voice naming, servos)
#   ./run.sh --no-servo    recognition only, servos stay still
HERE="$(cd "$(dirname "$0")" && pwd)"
source "$HERE/scripts/qnn_env.sh"
source "$HERE/.venv/bin/activate"
cd "$HERE"
python recognize.py watch "$@"
