# Troubleshooting

Every problem we hit while building Pip, with its fix.

## ExecuTorch and QNN

| Symptom | Cause | Fix |
|---|---|---|
| `Command '' not found, but can be installed with: ...` | `$QNN_RUNNER` is empty: new terminal without the environment | `source scripts/qnn_env.sh` |
| `runner MISSING`, no `~/executorch` | The guide's paths assume a prepared image under `/home/debian` | Our checkout was at `~/git/executorch`; `find / -name qnn_executor_runner` |
| `No matching distribution found for torchao==0.18.0.dev20260729` | Deleted nightly | Pin `torchao==0.18.0` in `install_requirements.py` and `requirements-ventuno.txt` |
| `torchao==...+xpu` | Intel GPU build pinned | Same fix |
| `No matching distribution found for torch==2.13.0+cpu` | `+cpu` builds aren't on PyPI | `--extra-index-url https://download.pytorch.org/whl/cpu --extra-index-url https://download.pytorch.org/whl/test/cpu` |
| `ModuleNotFoundError: No module named 'executorch'` | Checkout not on the path | `export PYTHONPATH=$HOME/git` |
| `export_example.py: error: ... -m/--model_name` | Wrong flags | `python export_example.py -m add -g --soc QCS8275 -f ~/model_output/` |
| `FileNotFoundError: 'flatc'` | FlatBuffers compiler missing | `sudo apt install flatbuffers-compiler` |
| `Environment variable QNN_SDK_ROOT must be set` | Export tools require it | `scripts/setup_qnn_sdk_links.sh`, `QNN_SDK_ROOT=$HOME/qnn_sdk` |
| `Cannot Open QNN library /usr/lib/x86_64-linux-clang/libQnnHtp.so` | Tools assume an x86 SDK layout | Same fake SDK root |
| `libqnn_executorch_backend.so: cannot open shared object file` | Runner can't find ExecuTorch's backend library | Add `build-x86/backends/qualcomm` to `LD_LIBRARY_PATH` |
| `no .jpg files in ...` | Calibration images missing or in another folder | `scripts/capture_calib.sh` and check the path |
| Low NPU vs CPU similarity (0.81) | 8-bit activations | Re-export with `--quant 16a8w` |

## Camera

| Symptom | Cause | Fix |
|---|---|---|
| Arducam ribbon camera: no `/dev/video*`, nothing in `dmesg` | No Qualcomm camera stack on this image (`gst-inspect-1.0 \| grep qti` finds nothing) | Use a USB webcam; ask for an image with camera support |
| `/dev/video32`, `/dev/video33` only | Those are the hardware video encoder/decoder (`msm_vidc`), not cameras | Plug in the webcam |
| `cv2` has no `CascadeClassifier` | OpenCV 5 moved it out of the main package | `pip install "opencv-python-headless<5"` (only needed for face detection experiments) |

## Servos

| Symptom | Cause | Fix |
|---|---|---|
| `cannot import name 'sms_sts' from 'scservo_sdk'` | pip `feetech-servo-sdk` is a slim SDK | Use `PacketHandler(0)` and register addresses (see `tools/servo_test.py`) |
| ID 1: `Incorrect status packet`, ID 2: `There is no status packet` | Both servos are ID 1 | `tools/set_id.py` with one servo connected |
| Positions read but no motion | No 12 V to the servos | Power the adapter's barrel jack or screw terminal |

## Bridge and buttons

| Symptom | Cause | Fix |
|---|---|---|
| `method set_leds not available` / `method ping not available` | MCU registered its functions before the Router reopened the serial link | The sketch's 40 s startup wait; start the robot after the LED stops blinking |
| Router log: `gpioset: invalid option -- 'c'` | Router script vs. GPIO tool version | Harmless here |
| Socket permission error | User not in the socket's group | `ls -l /var/run/arduino-router.sock`, add yourself to that group |

## Voice

| Symptom | Cause | Fix |
|---|---|---|
| `open() got an unexpected keyword argument 'metadata_errors'` | faster-whisper vs. PyAV version mismatch | `listen.py` reads the WAV with `wave` + NumPy and passes the array directly |
| Wrong or empty names | Quiet mic | Speak close to the webcam; `alsamixer -c 1` (F4) to raise capture volume; check with `arecord ... -V mono` |

## Recognition quality

| Symptom | Fix |
|---|---|
| Empty desk scores high for every object | Teach `nothing`; the mean-centering in `match()` removes shared background |
| Two objects score almost the same | Use more distinctive objects, teach more angles, raise `MARGIN` |
| Answer flickers | Already smoothed (2 of 3 frames); hold the object steady |
