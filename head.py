"""Pan-tilt head gestures on two Feetech STS3215 servos."""
import threading
import time

from scservo_sdk import PortHandler, PacketHandler

PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A46084709-if00"
PAN, TILT = 1, 2
CENTER = 2048
TORQUE, ACCEL, GOAL_POS, GOAL_SPEED = 40, 41, 42, 46


class Head:
    def __init__(self):
        self.port = PortHandler(PORT)
        assert self.port.openPort() and self.port.setBaudRate(1_000_000), "can't open servo port"
        self.bus = PacketHandler(0)
        self.lock = threading.Lock()
        self.busy = False
        for sid in (PAN, TILT):
            self.bus.write1ByteTxRx(self.port, sid, ACCEL, 40)
            self.bus.write2ByteTxRx(self.port, sid, GOAL_SPEED, 2000)
            self.bus.write1ByteTxRx(self.port, sid, TORQUE, 1)
        self.center()

    def _move(self, sid, offset):
        with self.lock:
            self.bus.write2ByteTxRx(self.port, sid, GOAL_POS, CENTER + offset)

    def center(self):
        self._move(PAN, 0)
        self._move(TILT, 0)

    def _play(self, steps):
        try:
            for sid, offset, pause in steps:
                self._move(sid, offset)
                time.sleep(pause)
            self.center()
            time.sleep(0.3)
        finally:
            self.busy = False

    def gesture(self, name):
        """Start a gesture in the background; ignored if one is already playing."""
        if self.busy:
            return
        steps = {
            # yes: two quick nods
            "nod": [(TILT, 200, 0.25), (TILT, -200, 0.25), (TILT, 200, 0.25), (TILT, -200, 0.25)],
            # no: two quick shakes
            "shake": [(PAN, 250, 0.25), (PAN, -250, 0.25), (PAN, 250, 0.25), (PAN, -250, 0.25)],
            # hmm?: look slightly aside and up, hold, come back
            "curious": [(PAN, 180, 0.3), (TILT, -150, 0.8)],
            # bored: slow look around
            "idle": [(PAN, -300, 0.8), (PAN, 300, 1.2)],
        }.get(name)
        if not steps:
            return
        self.busy = True
        threading.Thread(target=self._play, args=(steps,), daemon=True).start()

    def close(self):
        self.center()
        time.sleep(0.5)
        self.port.closePort()
