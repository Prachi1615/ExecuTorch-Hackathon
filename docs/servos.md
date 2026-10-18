# Servos

Two Feetech STS3215 (12 V) serial bus servos on a Waveshare bus servo adapter. Python uses the pip package `feetech-servo-sdk` (`scservo_sdk`). That package has `PortHandler` and `PacketHandler` but **not** the `sms_sts` helper class from Feetech's full SDK, so the code writes control-table registers directly.

## Control table addresses used

| Address | Register | Size |
|---|---|---|
| 5 | ID | 1 byte (EEPROM) |
| 40 | Torque enable | 1 |
| 41 | Acceleration | 1 |
| 42 | Goal position | 2 |
| 46 | Goal speed | 2 |
| 55 | EEPROM lock | 1 |
| 56 | Present position | 2 |

Positions run 0–4095 for 360°, with 2048 as center. Protocol: `PacketHandler(0)`, baud 1,000,000.

## Find the port

```bash
ls /dev/ttyACM* /dev/ttyUSB*
ls -l /dev/serial/by-id/
```

Use the `by-id` path in code (`usb-1a86_USB_Single_Serial_<serial>-if00`). It survives replugging. **Change the serial number in `head.py` and the tools to match your adapter.**

## Give each servo its own ID

**Symptom:** `servo 1 read: Incorrect status packet!` and `servo 2: There is no status packet!`

**Cause:** both servos are ID 1 (factory default), so both answer at once and their replies collide.

**Fix:** connect only one servo, then:

```bash
python tools/scan.py          # should find ID 1
python tools/set_id.py 1 2    # change it to ID 2
python tools/scan.py          # should find ID 2
```

Reconnect the other servo; `scan.py` should now find IDs 1 and 2. Label them: **1 = pan, 2 = tilt**.

## Test

Hold the servos down (12 V torque can flip them over), then:

```bash
python tools/servo_test.py
```

Expected: `servo 1: position ~2047`, `servo 2: position ~2046`, then a nod and a shake.

| Symptom | Cause |
|---|---|
| `can't open port` | permissions: `sudo usermod -aG dialout $USER`, then log in again |
| Positions read but nothing moves | no 12 V reaching the servos (USB powers the adapter's logic only) |
| `There is no status packet!` for every ID | jumper not in USB mode, wrong baud, or no servo power |

## Tuning gestures

Edit the offsets and pauses in `head.py`. When the head is mounted, check the tilt range by hand first so gestures can't hit the mount or pull the camera cable.
