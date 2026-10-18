"""List the IDs of all Feetech servos answering on the bus (IDs 0-20)."""
from scservo_sdk import PortHandler, PacketHandler, COMM_SUCCESS

PORT = "/dev/serial/by-id/usb-1a86_USB_Single_Serial_5A46084709-if00"
port = PortHandler(PORT)
assert port.openPort() and port.setBaudRate(1_000_000)
bus = PacketHandler(0)

for sid in range(0, 21):
    model, res, err = bus.ping(port, sid)
    if res == COMM_SUCCESS:
        print(f"found servo ID {sid}, model {model}")
port.closePort()
