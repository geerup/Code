"""AI Game Master server: POST an action, get narration + the new authoritative
state. Holds one in-memory session (demo). Serves the web client from web/.

    python server.py        # http://localhost:8080
"""
from __future__ import annotations

import json
import os
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from gm import GameMaster, OllamaLLM, demo_world

GM = GameMaster(OllamaLLM(os.environ.get("MODEL", "llama3.1")), demo_world())


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path in ("/", ""):
            return self._file("web/index.html", "text/html")
        if self.path == "/state":
            return self._json(200, GM.world.snapshot())
        return self._file("web" + self.path, "application/octet-stream")

    def do_POST(self):  # noqa: N802
        if self.path != "/action":
            return self._json(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        body = json.loads(self.rfile.read(length) or b"{}")
        turn = GM.act(str(body.get("action", "")))
        self._json(200, {"narration": turn.narration, "effects": turn.applied_effects, "state": turn.snapshot})

    def _file(self, path, ctype):
        try:
            with open(path, "rb") as f:
                self._raw(200, ctype, f.read())
        except OSError:
            self._raw(404, "text/plain", b"not found")

    def _json(self, code, body):
        self._raw(code, "application/json", json.dumps(body).encode())

    def _raw(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *a):
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"AI Game Master on :{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
