# Environment for ExecuTorch + Qualcomm QNN on the Arduino VENTUNO Q.
# Usage: source scripts/qnn_env.sh   (in every new terminal)
#
# Assumes an ExecuTorch checkout at ~/git/executorch with its venv in .venv
# and the runner already built in build-x86/ (on this board "build-x86" is
# really the native aarch64 build; the name comes from ExecuTorch's script).

source "$HOME/git/executorch/.venv/bin/activate"
export EXECUTORCH_ROOT="$HOME/git/executorch"
export PYTHONPATH="$HOME/git${PYTHONPATH:+:$PYTHONPATH}"
export MODEL_OUTPUT="$HOME/model_output"
export QNN_RUNNER="$EXECUTORCH_ROOT/build-x86/examples/qualcomm/executor_runner/qnn_executor_runner"
export LD_LIBRARY_PATH="$EXECUTORCH_ROOT/build-x86/backends/qualcomm${LD_LIBRARY_PATH:+:$LD_LIBRARY_PATH}"
export ADSP_LIBRARY_PATH=/usr/lib
# Fake SDK root (see scripts/setup_qnn_sdk_links.sh)
export QNN_SDK_ROOT="$HOME/qnn_sdk"
