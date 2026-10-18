# Using Pip

## Start

```bash
./run.sh
```

At startup you should see `model: .../dino16/dino_features.pte`, `microphone ready` and `buttons ready`.

`run.sh` passes flags through to `recognize.py watch`:

| Flag | Effect |
|---|---|
| `--no-servo` | servos stay still |
| `--no-buttons` | don't use the Bridge; keys only |

## Controls

| Button | Key | Does |
|---|---|---|
| A | `t` | **Learn:** LED A lights, say the name within 3 s, then hold the object up while it takes 8 photos (turn it a little between shots). Pip nods. |
| B | `f` | **Forget** everything except the empty-scene baseline. Pip shakes its head. |
| C | `p` | **Pause / resume.** Recognition keeps running but the head stays still. LED C shows paused. |

## Terminal commands

```bash
python recognize.py teach nothing    # teach the empty-scene baseline
python recognize.py teach mug        # teach from the terminal
python recognize.py forget           # forget all but the baseline
rm -f memory.npz                     # full reset, including the baseline
```

## Reading the output

```
I SEE: mug           | mug=0.54  phone=0.33  nothing=-0.39 | 0.56s
```

Scores are centered cosine similarities (see [architecture.md](architecture.md)). A name needs at least `0.30` and a lead of `0.08` over the runner-up. `...` means it hasn't settled yet (2 of the last 3 frames must agree).

To see what the camera sees, the latest frame is saved to `/tmp/last.jpg`. To view it from a laptop: `python3 -m http.server 8000` in `/tmp`, then open `http://<board-ip>:8000/last.jpg`.

## Tips for good recognition

- Teach `nothing` first, at the place where you'll demo.
- Hold objects **close and centered**: only the middle of the frame is used.
- Prefer **distinctive** objects: colorful, textured, different shapes. A dark phone with its screen off looks a lot like an empty desk; turn the screen on.
- Teach the same name twice from different angles to make it more reliable.
- Tune `THRESHOLD`, `MARGIN` and `ZOOM` at the top of `recognize.py`.

## Demo checklist

1. Power on the board and the 12 V servo supply.
2. Wait for the MCU's built-in LED to **stop fast-blinking** (~40 s after the MCU starts).
3. SSH in, `cd` to the repo.
4. `rm -f memory.npz` and `python recognize.py teach nothing` with the table empty (new place, new lighting).
5. `./run.sh`
6. Demo: A + "banana" + hold up the banana → nod. Take it away, bring it back → "I know this!" + nod. Show something unknown → curious look. B → shake, forgotten.
7. Between visitors: press B.

If the buttons stop responding, restart the App Lab app and wait for the blinking to stop, or use the keys.
