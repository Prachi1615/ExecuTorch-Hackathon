# Board setup: ExecuTorch + QNN on the VENTUNO Q

This is the path that worked on our board (hostname `QCVENTUNO009`, user `arduino`, Ubuntu on aarch64, Python 3.12). The track guide assumes a prepared image with files under `/home/debian`; ours had the stock image, so several fixes were needed. Each is below.

## What was already on the board

- **QNN SDK, installed system-wide:** headers in `/usr/include/QNN/`, runtime libraries such as `/usr/lib/libQnnHtp.so` (QNN API 2.38).
- **An ExecuTorch checkout** at `~/git/executorch` with a board-specific `requirements-ventuno.txt`, an aarch64 build of the QNN Python bindings (`backends/qualcomm/python/PyQnnManagerAdaptor.cpython-312-aarch64-linux-gnu.so`), and a built runner in `build-x86/` (despite the name, it's a native aarch64 build).

Check yours:

```bash
ls /usr/include/QNN/QnnInterface.h /usr/lib/libQnnHtp.so
find ~/git/executorch -name qnn_executor_runner -type f
file ~/git/executorch/build-x86/examples/qualcomm/executor_runner/qnn_executor_runner   # should say ARM aarch64
```

## 1. Python environment for ExecuTorch

```bash
cd ~/git/executorch
python3 -m venv .venv
source .venv/bin/activate
```

### Fix: pinned nightlies that no longer exist

`install_requirements.py` and `requirements-ventuno.txt` pinned `torchao==0.18.0.dev20260729`, a nightly that PyTorch's index had already deleted (and in `requirements-ventuno.txt` with a `+xpu` Intel GPU suffix, which doesn't exist for ARM). Use the stable release:

```bash
sed -i 's/TORCHAO_NIGHTLY_VERSION = "0.18.0.dev20260729"/TORCHAO_NIGHTLY_VERSION = "0.18.0"/' install_requirements.py
sed -i 's/^torchao==.*/torchao==0.18.0/' requirements-ventuno.txt
```

### Fix: `torch==2.13.0+cpu` not found

`+cpu` builds live on PyTorch's own index, not PyPI:

```bash
pip install -r requirements-ventuno.txt \
  --extra-index-url https://download.pytorch.org/whl/cpu \
  --extra-index-url https://download.pytorch.org/whl/test/cpu
```

(If that still fails, `sed -i 's/+cpu//g' requirements-ventuno.txt`: on ARM64 the PyPI build is CPU-only anyway.)

### Make the checkout importable

Installing the requirements doesn't install ExecuTorch itself. Put the checkout's **parent** folder on `PYTHONPATH`:

```bash
export PYTHONPATH="$HOME/git"
python -c "from executorch.backends.qualcomm.quantizer.quantizer import QnnQuantizer; print('ok')"
```

(`import executorch; print(executorch.__file__)` prints `None` because it's a namespace package. That's fine.)

### Fix: `flatc` not found

```bash
sudo apt install flatbuffers-compiler
```

## 2. QNN SDK root for export tools

Export scripts insist on `QNN_SDK_ROOT`, and then load `$QNN_SDK_ROOT/lib/x86_64-linux-clang/libQnnHtp.so`, an x86 PC layout. Setting `QNN_SDK_ROOT=/usr` fails. Fix it with a fake SDK root of symlinks (nothing in `/usr` is changed):

```bash
scripts/setup_qnn_sdk_links.sh
```

(Exporting `add.pte` worked earlier *without* `QNN_SDK_ROOT` set, because the library is then found on the normal library path. The DINOv2 export path requires the variable.)

## 3. Runner library path

The runner needs ExecuTorch's own QNN backend library:

```
error while loading shared libraries: libqnn_executorch_backend.so
```

Fix: add `~/git/executorch/build-x86/backends/qualcomm` to `LD_LIBRARY_PATH`.

## 4. One environment file

All of the above is in [`scripts/qnn_env.sh`](../scripts/qnn_env.sh). In every new terminal:

```bash
source scripts/qnn_env.sh
```

Forgetting this produces `Command '' not found, but can be installed with: ...`: `$QNN_RUNNER` is empty in the new shell.

## 5. Smoke test: the add model

```bash
source scripts/qnn_env.sh
cd ~/git/executorch/examples/qualcomm/scripts
python export_example.py -m add -g --soc QCS8275 -f ~/model_output/
mkdir -p ~/model_output/add-run/outputs && cd ~/model_output/add-run
"$QNN_RUNNER" --model_path ~/model_output/add.pte
```

Expected: `Model executed successfully`, `1 inferences took ~0.4 ms`. These lines are harmless:

- `Qnn API version 2.38.0 is used. The version is tested against 2.35.0.`
- `QnnContextCustomProtocol expected magic number ... but get ...`
- `E ... Output 0 is memory planned ... Cannot override the existing data pointer` (the runner ignores it)
- `backend_opinfo module couldn't be imported` and `register_constant()` deprecation warnings during export

`backend type 2` in the log is the HTP (NPU) backend.

## 6. Robot environment

Keep the robot's packages separate from ExecuTorch's:

```bash
cd <this repo>
python3 -m venv .venv
source .venv/bin/activate
pip install -r requirements.txt
sudo usermod -aG dialout $USER     # serial access for the servo adapter; log in again afterward
```

Next: [model-export.md](model-export.md)
