#!/usr/bin/env python3
"""Teach-and-recognize robot head: DINOv2 on the NPU, servo reactions,
Modulino buttons, voice naming, and an optional API for OM1.

  python recognize.py teach <name>   teach from the terminal
  python recognize.py watch          run the robot (Ctrl+C to stop)
      --api          serve the robot API on port 8765 (for OM1)
      --no-mic       don't use the microphone (e.g. when OM1 is using it)
      --no-servo     servos stay still
      --no-buttons   don't use the Modulino buttons
  python recognize.py forget         clear everything except the empty-scene baseline

While watching:
  A button or 't' = learn what's in front of me (say its name first)
  B button or 'f' = forget everything (keeps the baseline)
  C button or 'p' = pause / resume
"""
import os
import select
import subprocess
import sys
import termios
import time
import tty
from collections import deque

import cv2
import numpy as np
from PIL import Image

HERE = os.path.dirname(os.path.abspath(__file__))
_m16 = os.path.join(HERE, "dino16", "dino_features.pte")
MODEL = _m16 if os.path.exists(_m16) else os.path.join(HERE, "dino", "dino_features.pte")
MEMORY = os.path.join(HERE, "memory.npz")
WORK = "/tmp/dino_run"
RUNNER = os.environ["QNN_RUNNER"]

ZOOM = 0.6         # use only the middle 60% of the frame
THRESHOLD = 0.30   # minimum score to count as a match
MARGIN = 0.08      # winner must beat runner-up by this much
SHOTS = 8          # photos per teach
IDLE_AFTER = 15    # seconds of "nothing" before it looks around
BTN_A, BTN_B, BTN_C = 1, 2, 4
LED_TEACH, LED_PAUSE = 1, 4
GESTURES = ("nod", "shake", "curious", "idle")

MEAN = np.array([0.485, 0.456, 0.406], np.float32)
STD = np.array([0.229, 0.224, 0.225], np.float32)


# ---------- vision ----------
def preprocess(bgr):
    """Zoom to center, shorter side to 256, center crop 224, normalize."""
    h, w = bgr.shape[:2]
    ch, cw = int(h * ZOOM), int(w * ZOOM)
    y0, x0 = (h - ch) // 2, (w - cw) // 2
    bgr = bgr[y0:y0 + ch, x0:x0 + cw]
    img = Image.fromarray(cv2.cvtColor(bgr, cv2.COLOR_BGR2RGB))
    w, h = img.size
    s = 256 / min(w, h)
    img = img.resize((int(w * s), int(h * s)), Image.BILINEAR)
    w, h = img.size
    left, top = (w - 224) // 2, (h - 224) // 2
    img = img.crop((left, top, left + 224, top + 224))
    x = (np.asarray(img, np.float32) / 255.0 - MEAN) / STD
    return x.transpose(2, 0, 1)[None].astype(np.float32)


def embed(bgr):
    """Run DINOv2 on the NPU and return a normalized 384-number fingerprint."""
    os.makedirs(f"{WORK}/outputs", exist_ok=True)
    preprocess(bgr).tofile(f"{WORK}/input_0_0.raw")
    with open(f"{WORK}/input_list.txt", "w") as f:
        f.write("input_0_0.raw\n")
    subprocess.run(
        [RUNNER, "--model_path", MODEL, "--input_list_path", "input_list.txt",
         "--output_folder_path", "outputs"],
        cwd=WORK, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
    )
    v = np.fromfile(f"{WORK}/outputs/output_0_0.raw", np.float32)
    return v / (np.linalg.norm(v) + 1e-8)


def match(v, names, vecs):
    """Best score per learned name, after removing what all memories share."""
    mean = vecs.mean(axis=0)

    def center(x):
        x = x - mean
        return x / (np.linalg.norm(x, axis=-1, keepdims=True) + 1e-8)

    sims = center(vecs) @ center(v)
    scores = {}
    for name, s in zip(names, sims):
        scores[name] = max(scores.get(name, -1.0), float(s))
    return sorted(scores.items(), key=lambda kv: -kv[1])


# ---------- memory ----------
def load_memory():
    if os.path.exists(MEMORY):
        d = np.load(MEMORY)
        return list(d["names"]), d["vecs"]
    return [], np.zeros((0, 384), np.float32)


def save_memory(names, vecs):
    np.savez(MEMORY, names=np.array(names), vecs=vecs)


def forget_all_but_baseline():
    names, vecs = load_memory()
    keep = [i for i, n in enumerate(names) if n == "nothing"]
    save_memory([names[i] for i in keep],
                vecs[keep] if keep else np.zeros((0, 384), np.float32))


def next_auto_name(names):
    taken = {n for n in names if n != "nothing"}
    i = 1
    while f"thing {i}" in taken:
        i += 1
    return f"thing {i}"


def known_objects(names):
    return sorted(set(names) - {"nothing"})


# ---------- camera ----------
def open_camera():
    cap = cv2.VideoCapture(0, cv2.CAP_V4L2)
    cap.set(cv2.CAP_PROP_FRAME_WIDTH, 640)
    cap.set(cv2.CAP_PROP_FRAME_HEIGHT, 480)
    cap.set(cv2.CAP_PROP_BUFFERSIZE, 1)
    assert cap.isOpened(), "can't open camera"
    for _ in range(5):
        cap.read()
    return cap


def fresh_frame(cap):
    for _ in range(2):
        cap.grab()          # drop stale frames
    ok, frame = cap.read()
    assert ok, "camera read failed"
    return frame


def capture_shots(cap, name):
    vecs = []
    for i in range(SHOTS):
        print(f"  shot {i + 1}/{SHOTS}: move or turn it a little...")
        time.sleep(0.6)
        frame = fresh_frame(cap)
        vecs.append(embed(frame))
        cv2.imwrite(f"/tmp/teach_{name.replace(' ', '_')}_{i}.jpg", frame)
    return vecs


def teach(name):
    names, vecs = load_memory()
    cap = open_camera()
    new = capture_shots(cap, name)
    cap.release()
    save_memory(names + [name] * SHOTS, np.vstack([vecs] + new))
    print(f"learned '{name}'. Known: {sorted(set(names + [name]))}")


# ---------- keyboard backup for the buttons ----------
def read_keys():
    """Keys pressed in the terminal, as button bits: t = A, f = B, p = C."""
    bits = 0
    while select.select([sys.stdin], [], [], 0)[0]:
        ch = sys.stdin.read(1).lower()
        bits |= {"t": BTN_A, "f": BTN_B, "p": BTN_C}.get(ch, 0)
    return bits


# ---------- robot loop ----------
def watch(use_servos=True, use_buttons=True, use_mic=True, use_api=False):
    print(f"model: {MODEL}")

    listen_for_name = None
    if use_mic:
        try:
            from listen import listen_for_name, load as load_speech
            load_speech()
            print("microphone ready")
        except Exception as e:
            print(f"microphone unavailable ({e}); objects get automatic names")
            listen_for_name = None

    head = None
    if use_servos:
        from head import Head
        head = Head()

    bridge = None
    if use_buttons:
        try:
            from bridge import Bridge
            bridge = Bridge()
            bridge.call("set_leds", 0)
            print("buttons ready")
        except Exception as e:
            print(f"buttons unavailable ({e}); use keys t / f / p")
            bridge = None

    api = None
    if use_api:
        from api import RobotAPI
        api = RobotAPI()

    paused = False

    def gesture(name):
        if head and not paused and name in GESTURES:
            head.gesture(name)

    def leds(mask):
        if bridge:
            try:
                bridge.call("set_leds", mask)
            except Exception:
                pass

    def announce(text):
        print(f">>> {text}")
        if api:
            api.event(text)

    names, vecs = load_memory()
    if api:
        api.update(known=known_objects(names))
    cap = open_camera()
    old_term = termios.tcgetattr(sys.stdin) if sys.stdin.isatty() else None
    if old_term:
        tty.setcbreak(sys.stdin)    # read single keypresses without Enter

    recent = deque(maxlen=3)
    current, last_change = "nothing", time.time()
    try:
        while True:
            t0 = time.time()

            # --- gather commands: buttons, keyboard, API ---
            pressed = 0
            if bridge:
                try:
                    pressed = bridge.call("take_buttons") or 0
                except Exception as e:
                    print(f"button read failed: {e}")
            pressed |= read_keys()

            actions = []
            if pressed & BTN_C:
                actions.append(("pause", {}))
            if pressed & BTN_A:
                actions.append(("teach", {"voice": True}))
            if pressed & BTN_B:
                actions.append(("forget", {}))
            if api:
                actions += api.pop_commands()

            changed_memory = False
            for cmd, data in actions:
                if cmd == "pause":
                    paused = bool(data["paused"]) if "paused" in data else not paused
                    leds(LED_PAUSE if paused else 0)
                    if head:
                        head.center()
                    announce("paused" if paused else "resumed")
                    if api:
                        api.update(paused=paused)

                elif cmd == "gesture":
                    gesture(str(data.get("name", "")))

                elif cmd == "teach":
                    leds(LED_TEACH | (LED_PAUSE if paused else 0))
                    name = str(data.get("name", "")).strip().lower()
                    if not name and data.get("voice") and listen_for_name:
                        print(">>> say its name now...")
                        try:
                            name = listen_for_name()
                        except Exception as e:
                            print(f"mic failed: {e}")
                    name = name or next_auto_name(names)
                    print(f">>> learning '{name}'... hold it up")
                    new = capture_shots(cap, name)
                    names, vecs = names + [name] * SHOTS, np.vstack([vecs] + new)
                    save_memory(names, vecs)
                    leds(LED_PAUSE if paused else 0)
                    announce(f"learned {name}")
                    if api:
                        api.update(known=known_objects(names), seeing=name)
                    gesture("nod")
                    current = name
                    changed_memory = True

                elif cmd == "forget":
                    forget_all_but_baseline()
                    names, vecs = load_memory()
                    announce("forgot everything")
                    if api:
                        api.update(known=[], seeing="nothing")
                    gesture("shake")
                    current = "nothing"
                    changed_memory = True

            if changed_memory:
                recent.clear()
                continue

            # --- recognition ---
            if head and head.busy:          # don't judge blurry frames mid-gesture
                time.sleep(0.05)
                continue
            if len(set(names)) < 2:
                print("teach me something: hold it up and press A (or 't')")
                time.sleep(1)
                continue

            frame = fresh_frame(cap)
            ranked = match(embed(frame), names, vecs)
            best, score = ranked[0]
            second = ranked[1][1] if len(ranked) > 1 else -1.0
            guess = best if (score >= THRESHOLD and score - second >= MARGIN) else "unknown"
            recent.append(guess)
            steady = max(set(recent), key=recent.count)
            is_steady = recent.count(steady) >= 2

            if is_steady and steady != current:
                current, last_change = steady, time.time()
                if steady == "unknown":
                    announce("I see something I don't know")
                    gesture("curious")
                elif steady == "nothing":
                    announce("nothing in front of me")
                else:
                    announce(f"I see {steady}")
                    gesture("nod")
            elif current == "nothing" and time.time() - last_change > IDLE_AFTER:
                gesture("idle")
                last_change = time.time()

            if api:
                api.update(seeing=current, score=round(score, 3))

            verdict = f"I SEE: {steady}" if is_steady and steady != "unknown" else "..."
            detail = "  ".join(f"{n}={s:.2f}" for n, s in ranked)
            tag = " [paused]" if paused else ""
            print(f"{verdict:<20} | {detail} | {time.time() - t0:.2f}s{tag}")
            cv2.imwrite("/tmp/last.jpg", frame)
    except KeyboardInterrupt:
        pass
    finally:
        if old_term:
            termios.tcsetattr(sys.stdin, termios.TCSADRAIN, old_term)
        cap.release()
        leds(0)
        if api:
            api.close()
        if bridge:
            bridge.close()
        if head:
            head.close()


if __name__ == "__main__":
    cmd = sys.argv[1] if len(sys.argv) > 1 else "watch"
    if cmd == "teach" and len(sys.argv) > 2:
        teach(" ".join(sys.argv[2:]))
    elif cmd == "forget":
        forget_all_but_baseline()
        print("memory cleared (kept the empty-scene baseline)")
    else:
        watch(use_servos="--no-servo" not in sys.argv,
              use_buttons="--no-buttons" not in sys.argv,
              use_mic="--no-mic" not in sys.argv,
              use_api="--api" in sys.argv)
