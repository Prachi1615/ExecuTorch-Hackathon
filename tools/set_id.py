"""Change a servo's ID. Connect ONLY that servo to the bus first.

New Feetech servos all ship as ID 1; two servos with the same ID answer at the
same time and garble each other ("Incorrect status packet")."""
import sys

from scservo_sdk import PortHandler, PacketHandler

PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A46084709-if00"
OLD_ID = int(sys.argv[1]) if len(sys.argv) > 1 else 1
NEW_ID = int(sys.argv[2]) if len(sys.argv) > 2 else 2
ID_ADDR, LOCK_ADDR = 5, 55

port = PortHandler(PORT)
assert port.openPort() and port.setBaudRate(1_000_000)
bus = PacketHandler(0)

bus.write1ByteTxRx(port, OLD_ID, LOCK_ADDR, 0)   # unlock EEPROM
bus.write1ByteTxRx(port, OLD_ID, ID_ADDR, NEW_ID)
bus.write1ByteTxRx(port, NEW_ID, LOCK_ADDR, 1)   # lock EEPROM so it survives power-off
port.closePort()
print(f"done: ID {OLD_ID} -> {NEW_ID}")
