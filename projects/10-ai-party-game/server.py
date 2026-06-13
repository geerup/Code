"""Multiplayer AI party-game server (stdlib http). Clients poll /state; the host
starts rounds and reveals. One process can host many room codes.

    python server.py        # http://localhost:8080
"""
from __future__ import annotations

import json
import os
import random
import string
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from party import Room, RoomError
from party.judge import LLMJudge

ROOMS: dict[str, Room] = {}
JUDGE = LLMJudge(os.environ.get("MODEL", "llama3.1"))


def new_code() -> str:
    return "".join(random.choices(string.ascii_uppercase, k=4))


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path in ("/", ""):
            return self._file("web/index.html", "text/html")
        if self.path.startswith("/state/"):
            room = ROOMS.get(self.path.split("/")[-1].upper())
            return self._json(200, room.snapshot()) if room else self._json(404, {"error": "no room"})
        return self._file("web" + self.path, "application/octet-stream")

    def do_POST(self):  # noqa: N802
        body = self._body()
        try:
            if self.path == "/create":
                code = new_code()
                ROOMS[code] = Room(code=code)
                return self._json(200, {"code": code})
            parts = self.path.strip("/").split("/")
            room = ROOMS.get((parts[1] if len(parts) > 1 else "").upper())
            if room is None:
                return self._json(404, {"error": "no room"})
            action = parts[0]
            if action == "join":
                p = room.join(body["player_id"], body["name"])
                return self._json(200, {"ok": True, "name": p.name})
            if action == "start":
                room.start_round()
                return self._json(200, room.snapshot())
            if action == "submit":
                room.submit(body["player_id"], body["answer"])
                return self._json(200, {"ok": True})
            if action == "reveal":
                results = room.reveal(JUDGE)
                return self._json(200, {"results": results, "state": room.snapshot()})
            return self._json(404, {"error": "unknown action"})
        except RoomError as e:
            return self._json(400, {"error": str(e)})
        except (KeyError, json.JSONDecodeError):
            return self._json(400, {"error": "bad request"})

    def _body(self):
        length = int(self.headers.get("Content-Length", 0))
        return json.loads(self.rfile.read(length) or b"{}")

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
    print(f"AI party game on :{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
