# Pip: a robot head you can teach in seconds

Presentation - https://docs.google.com/presentation/d/1t9mUHzNZJa9VeZlJB3thjMR-OSlW5Bqb-GC11URJn4g/edit?slide=id.p1#slide=id.p1

Pip is a small pan-tilt robot head built on the **Arduino VENTUNO Q**. Hold up any object, press a button and say its name: Pip takes a few photos, learns it on the spot, and from then on nods when it sees it again. Show it something it doesn't know and it gives you a curious look.

Everything runs **on the board**: no training step and no cloud for vision.

- **Sees** with DINOv2 running on the Qualcomm Hexagon **NPU** through ExecuTorch (about 5 ms per image)
- **Learns** new objects from a few examples, using DINOv2 image fingerprints and nearest-neighbor matching
- **Hears** object names offline with Whisper on the CPU
- **Moves** with two Feetech STS3215 servos (pan and tilt) for nods, shakes and curious looks
- **Takes input** from Modulino Buttons read by the board's STM32 **microcontroller**, sent to Linux over the Arduino Bridge

Built for the IoT track: on-device AI + real-time sensing and control + connected experiences.

## How it works

```
 Webcam ──► crop + normalize ──► DINOv2 (ExecuTorch, QNN HTP NPU) ──► 384-number fingerprint
                                                                          │
                     memory.npz (fingerprints per learned name) ◄── teach │ compare
                                                                          ▼
 Modulino Buttons ──► STM32 MCU ──Bridge──► Linux loop ──► decision ──► servos (nod / shake / curious)
 Webcam mic ──► Whisper (CPU) ──► object name ┘
```

Details: [docs/architecture.md](docs/architecture.md)

## Hardware

| Part | Role |
|---|---|
| Arduino VENTUNO Q (Qualcomm Dragonwing IQ8 + STM32H5) | Linux + NPU for vision, MCU for buttons |
| Logitech Brio 101 USB webcam | Camera and microphone |
| 2× Feetech STS3215 (12 V) serial bus servos | Pan (ID 1) and tilt (ID 2) |
| Waveshare bus servo adapter + 12 V / 5 A supply | Drives the servo bus over USB |
| Arduino Modulino Buttons (Qwiic) | A = learn, B = forget, C = pause |

Wiring and power: [docs/hardware-setup.md](docs/hardware-setup.md)

## Using it

```bash
./run.sh
```

| Control | Does |
|---|---|
| **A** (or `t`) | Say the object's name, then hold it up while Pip takes 8 photos |
| **B** (or `f`) | Forget everything learned (keeps the empty-scene baseline) |
| **C** (or `p`) | Pause / resume all movement |

Full guide and demo checklist: [docs/usage.md](docs/usage.md)

## Setting it up from scratch

1. [Board setup](docs/board-setup.md): ExecuTorch, QNN runtime and the fixes this board needs
2. [Model export](docs/model-export.md): DINOv2 features for the NPU, calibrated on your own camera images
3. [Servos](docs/servos.md): IDs, power and testing
4. [Bridge and buttons](docs/bridge-and-buttons.md): the microcontroller sketch, and the startup timing gotcha
5. [Usage](docs/usage.md)
6. [Troubleshooting](docs/troubleshooting.md): every problem we hit and its fix

## Repository layout

```
recognize.py        main loop: camera, NPU recognition, teaching, reactions, inputs
head.py             servo gestures (nod, shake, curious, idle)
bridge.py           MessagePack-RPC client for the Arduino Router (Linux -> MCU)
listen.py           offline speech-to-text for object names (faster-whisper)
run.sh              one-command start
requirements.txt    robot Python dependencies
mcu/robot_buttons/  microcontroller sketch (Arduino App Lab)
export/             DINOv2 export script for ExecuTorch + QNN, and an NPU check
tools/              servo test, ID scan, ID change
scripts/            environment, QNN SDK link fix, calibration capture
docs/               documentation
```

## Results

- **NPU inference:** about 5 ms per image for DINOv2-small (16-bit activations, 8-bit weights)
- **NPU vs CPU:** DINOv2-small takes **6.3 ms** per image on the Hexagon NPU (ExecuTorch + QNN, 16-bit activations, 8-bit weights) vs **684 ms** in PyTorch on the board's CPU: **~108× faster**
- **Full recognition step:** about 0.5 s, dominated by starting the ExecuTorch runner process for each frame
- **Teaching:** 8 photos, about 6 seconds, no training
- **8-bit vs 16-bit:** 8a8w quantization gave only 0.81 cosine similarity to the CPU model; 16a8w is used instead
