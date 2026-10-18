# Hardware setup

## VENTUNO Q connections

| What | Where |
|---|---|
| Board power | 12–24 V DC into the barrel jack (also possible: 5 V/3 A USB-C, or 7–24 V screw terminal) |
| Webcam (Brio 101) | USB-A port |
| Servo adapter | USB-A port (via its USB-C cable) |
| Modulino Buttons | Qwiic connector |
| Network | Wi-Fi or Ethernet; SSH in from a laptop |
| Fan | Fan connector (the board has an active cooler; keep it connected when running models) |

The two USB-A ports are both used (webcam + servo adapter). Anything else needs a powered hub.

## Servos

- Two **Feetech STS3215, 12 V version** (the servos used in LeRobot arms).
- Daisy-chained: adapter → servo 1 → servo 2.
- **ID 1 = pan** (bottom), **ID 2 = tilt** (on top). New servos all ship as ID 1, so one must be changed: see [servos.md](servos.md).

### Waveshare bus servo adapter

- **Data:** USB-C to the VENTUNO Q. It shows up as `/dev/ttyACM0`, or more reliably as `/dev/serial/by-id/usb-1a86_USB_Single_Serial_<serial>-if00` (CH34x chip, vendor ID 1a86).
- **Power:** a separate **12 V, ≥5 A** supply into the adapter's barrel jack (5.5 × 2.1 mm, center positive) **or** its green screw terminal (match + and −). Never both at once.
- The **red LED** lights from USB alone. That only powers the logic, not the motors.
- **Jumper:** set to the USB control position (usually marked **A**).
- Never power the servos from the VENTUNO Q.

Power-up order: jumper on USB mode → USB-C to the board → 12 V supply last.

## Camera

We used the **Logitech Brio 101 USB webcam** (`/dev/video0`; `/dev/video1` is its metadata stream). It also provides the microphone (ALSA card `B101`).

**MIPI ribbon cameras (e.g. Arducam) did not work** on this board image: there is no Qualcomm camera stack installed (no `qtiqmmfsrc` GStreamer plugin, no camera services), so ribbon cameras don't appear as video devices. See [troubleshooting.md](troubleshooting.md).

## Audio

The Raspberry Pi audio HAT we brought didn't fit, so there's no speaker. The webcam's built-in mic is used for voice naming.

## Mounting

No brackets were available. A pan-tilt head can be improvised: pan servo taped or zip-tied flat on a heavy base, tilt servo attached sideways to the pan horn, camera taped to the tilt horn, with slack in the cables. For recognition demos, it also works with the camera fixed on the desk and the servos acting as an expressive "head."
