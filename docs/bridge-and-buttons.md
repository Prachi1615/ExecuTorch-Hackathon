# Bridge and Modulino Buttons

The Modulino Buttons are read by the STM32 microcontroller. Linux asks the MCU for presses through the **Arduino Router**, a Linux service that routes MessagePack-RPC calls between processes and the MCU.

```
Python (bridge.py) ──Unix socket──► arduino-router ──/dev/ttySTM0──► MCU sketch (Bridge.provide)
```

## MCU sketch

[`mcu/robot_buttons/sketch.ino`](../mcu/robot_buttons/sketch.ino). Create an app in **Arduino App Lab**, add the **Modulino** library, paste the sketch and press Run. App Lab's default `main.py` ("Hello world!") can stay as it is; it isn't used.

It registers:

| Function | Returns |
|---|---|
| `ping()` | 2 = bridge and buttons OK, 1 = bridge OK but buttons not found |
| `take_buttons()` | bitmask of presses since the last call: A=1, B=2, C=4 |
| `set_leds(mask)` | sets button LEDs: A=1, B=2, C=4 |

Presses are **latched** on the MCU, so a short press between two polls from Linux isn't lost.

## The startup timing problem (important)

**Symptom:** every call from Linux fails with `[2, 'method ping not available']`, even with the sketch running. The Router log shows the serial link opening but no functions registered.

**Cause:** after flashing, the MCU starts immediately and registers its functions in `setup()`, but the Router reopens the serial link about 25–30 s later. Registrations sent before that are lost, and `setup()` never runs again. The same happens at power-up, because Linux boots much slower than the MCU.

```
09:57:05  link closes (MCU is being flashed)       ← MCU starts, registers functions → lost
09:57:34  Router reopens /dev/ttySTM0
```

**Fix:** the sketch blinks the built-in LED fast for **40 seconds** before calling `Bridge.begin()` and registering. Start `recognize.py` only after the blinking stops.

## Testing

```bash
source .venv/bin/activate
python -c "from bridge import Bridge; print('ping:', Bridge().call('ping'))"
python -c "
import time
from bridge import Bridge
b = Bridge()
b.call('set_leds', 7); time.sleep(1); b.call('set_leds', 0)
for _ in range(10):
    print('pressed:', b.call('take_buttons')); time.sleep(0.5)
"
```

## Debugging

```bash
systemctl status arduino-router
journalctl -u arduino-router -f       # watch while restarting the App Lab app
ls -l /var/run/arduino-router.sock     # socket permissions
```

- `gpioset: invalid option -- 'c'` in the Router log is a mismatch between the Router's startup script and the installed GPIO tool. It didn't stop the serial link from working.
- The Router's guide mentions `/dev/ttyHS1` and `Serial1`; on our board the Router used **`/dev/ttySTM0`**.
- More detail: add `--verbose` to the Router's `ExecStart` with `sudo systemctl edit arduino-router` (clear `ExecStart=` first), then `daemon-reload` and `restart`.
- A diagnostic sketch that only registers `ping` and blinks slowly (bridge OK) or fast (`Bridge.begin()` failed) helps separate Bridge problems from Modulino problems.
- Don't call `Bridge.call()` or `Monitor.print()` inside a provided function: nested RPC can deadlock the link.

## Fallback

If the Bridge isn't available, `recognize.py` prints `buttons unavailable` and the keys `t` / `f` / `p` do the same as A / B / C.
