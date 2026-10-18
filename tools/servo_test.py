"""Check both servos answer, then center them and play a nod and a shake.
Hold the servos down when you run it: they move with 12 V torque."""
import time

from scservo_sdk import PortHandler, PacketHandler, COMM_SUCCESS

PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A46084709-if00"
BAUD = 1_000_000
PAN, TILT = 1, 2
CENTER = 2048                      # 0-4095 = 0-360 degrees

# STS3215 control table addresses
TORQUE_ENABLE, ACCEL, GOAL_POS, GOAL_SPEED, PRESENT_POS = 40, 41, 42, 46, 56

port = PortHandler(PORT)
assert port.openPort() and port.setBaudRate(BAUD), "can't open port"
bus = PacketHandler(0)             # protocol 0 = STS series


def check(sid, res, err, what):
    if res != COMM_SUCCESS or err != 0:
        print(f"servo {sid} {what}: {bus.getTxRxResult(res)} {bus.getRxPacketError(err)}")


for sid in (PAN, TILT):
    pos, res, err = bus.read2ByteTxRx(port, sid, PRESENT_POS)
    check(sid, res, err, "read")
    print(f"servo {sid}: position {pos}")
    check(sid, *bus.write1ByteTxRx(port, sid, ACCEL, 50), "accel")
    check(sid, *bus.write2ByteTxRx(port, sid, GOAL_SPEED, 1500), "speed")
    check(sid, *bus.write1ByteTxRx(port, sid, TORQUE_ENABLE, 1), "torque")


def move(sid, pos):
    check(sid, *bus.write2ByteTxRx(port, sid, GOAL_POS, pos), "move")


move(PAN, CENTER); move(TILT, CENTER); time.sleep(1)

for _ in range(2):                 # nod "yes"
    move(TILT, CENTER + 250); time.sleep(0.4)
    move(TILT, CENTER - 250); time.sleep(0.4)
move(TILT, CENTER); time.sleep(0.5)

for _ in range(2):                 # shake "no"
    move(PAN, CENTER + 300); time.sleep(0.4)
    move(PAN, CENTER - 300); time.sleep(0.4)
move(PAN, CENTER); time.sleep(0.5)

port.closePort()
