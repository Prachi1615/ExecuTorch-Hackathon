# Architecture

## The two brains of the VENTUNO Q

The VENTUNO Q has two processors, and Pip uses both:

| | Qualcomm Dragonwing IQ8 (Linux) | STM32H5 microcontroller |
|---|---|---|
| Runs | Ubuntu, Python, ExecuTorch | Arduino sketch on Zephyr |
| Pip uses it for | Camera, DINOv2 on the Hexagon NPU, speech-to-text, decisions, servo commands | Reading the Modulino Buttons, driving their LEDs |
| Link | Arduino Router (`/var/run/arduino-router.sock`) | Arduino Bridge over `/dev/ttySTM0` |

The servos are driven from Linux through a USB bus-servo adapter rather than from the MCU. That was the quickest path, and gestures don't need sub-millisecond timing.

## Recognition pipeline

1. **Grab a frame** at 640×480 from the webcam (stale buffered frames are dropped first).
2. **Preprocess** (`recognize.py: preprocess`): keep the center 60% (`ZOOM`) so the held object fills the picture instead of the desk, resize the short side to 256, center-crop 224×224, normalize with ImageNet mean/std, write a raw float32 NCHW tensor.
3. **Run DINOv2-small on the NPU** by calling `qnn_executor_runner` on `dino16/dino_features.pte`. The output is DINOv2's pooled CLS feature: 384 numbers, then L2-normalized. The model is exported without the ImageNet classifier; see [model-export.md](model-export.md).
4. **Compare with memory** (`match`): every stored fingerprint and the new one have the **mean of all stored fingerprints subtracted** before cosine similarity. That removes what every image shares (the desk, the room, the lighting), so the comparison focuses on the object. Each learned name scores its best-matching example.
5. **Decide**: the top name counts only if its score is at least `THRESHOLD` (0.30) **and** beats the runner-up by `MARGIN` (0.08); otherwise "unknown".
6. **Smooth**: an answer is acted on only when 2 of the last 3 frames agree, so the head doesn't twitch.
7. **React on change**: a known object gives a nod, unknown gives a curious look, and 15 s of nothing gives a slow look around.

### Why DINOv2 features and not a classifier

DINOv2's self-supervised features are very good at "is this the same kind of thing I saw before?" from a handful of examples. That makes teaching a new object instant: just store a few fingerprints. A classifier would only know its fixed 1,000 ImageNet labels.

### The "nothing" baseline

The first thing taught is `nothing`: the empty scene. Without it, an empty desk always "matches" whichever object looks closest. It also anchors the mean used for centering. Re-teach it whenever the location or lighting changes.

## Teaching

Pressing **A** (or `t`):

1. Lights button LED A.
2. If no name was given and the mic is on, records 3 s and transcribes it with Whisper `base.en` (int8, CPU), dropping filler like "it's a" and "this is the".
3. Takes 8 photos about 0.6 s apart (move the object slightly between them) and stores 8 fingerprints under that name in `memory.npz`.
4. Nods.

Teaching an existing name again adds more examples to it, which makes it more reliable.

## Gestures

`head.py` plays gestures in a background thread so recognition keeps running. While a gesture plays, recognition pauses, because frames would be blurry if the camera is mounted on the head.

| Gesture | Motion |
|---|---|
| `nod` | tilt ±200 ticks, twice |
| `shake` | pan ±250 ticks, twice |
| `curious` | pan +180, tilt −150, hold |
| `idle` | slow pan left and right |

4096 ticks = 360°, so 200 ticks ≈ 18°.

## Inputs

The main loop checks two input sources each cycle:

- Modulino Buttons through the Bridge (`take_buttons` returns presses latched since the last call, so short presses aren't missed between polls)
- Keyboard keys `t`, `f`, `p` (backup if the Bridge isn't available)

## Performance

| Step | Time |
|---|---|
| DINOv2 on the NPU | ~5 ms |
| Runner start + model load (per frame) | ~250 ms |
| Full loop iteration | ~0.5 s |

The runner is started as a separate process for every frame, which dominates the time. Loading the model once through ExecuTorch's runtime bindings would bring recognition close to real time; that's the obvious next optimization.
