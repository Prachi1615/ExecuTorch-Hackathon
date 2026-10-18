"""Minimal MessagePack-RPC client for the Arduino Router (Linux -> MCU calls)."""
import itertools
import socket

import msgpack

SOCK = "/var/run/arduino-router.sock"


class Bridge:
    def __init__(self, timeout=1.0):
        self.s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        self.s.connect(SOCK)
        self.s.settimeout(timeout)
        self.unpacker = msgpack.Unpacker(raw=False)
        self.ids = itertools.count(1)

    def call(self, method, *args):
        msgid = next(self.ids)
        self.s.sendall(msgpack.packb([0, msgid, method, list(args)]))
        while True:
            for msg in self.unpacker:
                if msg[0] == 1 and msg[1] == msgid:
                    if msg[2]:
                        raise RuntimeError(f"{method}: {msg[2]}")
                    return msg[3]
            data = self.s.recv(4096)
            if not data:
                raise ConnectionError("router closed the connection")
            self.unpacker.feed(data)

    def close(self):
        self.s.close()
