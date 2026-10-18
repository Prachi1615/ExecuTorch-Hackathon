"""Small local HTTP API so OM1 (or anything else) can see what the robot sees and make it act."""
import json
import queue
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

COMMANDS = ("gesture", "teach", "forget", "pause")


class RobotAPI:
    def __init__(self, host="0.0.0.0", port=8765):
        self.commands = queue.Queue()
        self.lock = threading.Lock()
        self.state = {"seeing": "nothing", "score": 0.0, "known": [], "paused": False,
                      "event": "", "event_id": 0, "time": time.time()}
        api = self

        class Handler(BaseHTTPRequestHandler):
            def log_message(self, *args):
                pass

            def _send(self, code, obj):
                body = json.dumps(obj).encode()
                self.send_response(code)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(body)))
                self.end_headers()
                self.wfile.write(body)

            def do_GET(self):
                if self.path == "/state":
                    self._send(200, api.get_state())
                else:
                    self._send(404, {"error": "not found"})

            def do_POST(self):
                length = int(self.headers.get("Content-Length", 0) or 0)
                try:
                    data = json.loads(self.rfile.read(length) or b"{}")
                except json.JSONDecodeError:
                    return self._send(400, {"error": "bad json"})
                cmd = self.path.strip("/")
                if cmd not in COMMANDS:
                    return self._send(404, {"error": f"unknown command, use one of {COMMANDS}"})
                api.commands.put((cmd, data if isinstance(data, dict) else {}))
                self._send(200, {"ok": True})

        self.server = ThreadingHTTPServer((host, port), Handler)
        threading.Thread(target=self.server.serve_forever, daemon=True).start()
        print(f"robot API on http://{host}:{port}")

    def get_state(self):
        with self.lock:
            return dict(self.state)

    def update(self, **fields):
        with self.lock:
            self.state.update(fields)
            self.state["time"] = time.time()

    def event(self, text):
        with self.lock:
            self.state["event"] = text
            self.state["event_id"] += 1
            self.state["time"] = time.time()

    def pop_commands(self):
        out = []
        while True:
            try:
                out.append(self.commands.get_nowait())
            except queue.Empty:
                return out

    def close(self):
        self.server.shutdown()
