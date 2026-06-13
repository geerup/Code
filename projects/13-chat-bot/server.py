"""Webhook server (stdlib http.server) for a Telegram bot.

Set TELEGRAM_TOKEN and point Telegram's webhook at /webhook. Replies are sent
back via the Telegram Bot API. The whole thing is one process — deploy as a Fly
worker.

    python server.py        # listens on :8080
"""
from __future__ import annotations

import json
import os
import urllib.request
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from bot import Bot, OllamaLLM, telegram

TOKEN = os.environ.get("TELEGRAM_TOKEN", "")
BOT = Bot(OllamaLLM(os.environ.get("MODEL", "llama3.1")))


def send_message(payload: dict) -> None:
    if not TOKEN:
        print("[dry-run] would send:", payload)
        return
    req = urllib.request.Request(
        f"https://api.telegram.org/bot{TOKEN}/sendMessage",
        data=json.dumps(payload).encode(),
        headers={"Content-Type": "application/json"},
    )
    urllib.request.urlopen(req, timeout=30)  # noqa: S310


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802 - health check
        self._json(200, {"ok": True, "service": "chat-bot"})

    def do_POST(self):  # noqa: N802
        if self.path != "/webhook":
            return self._json(404, {"error": "not found"})
        length = int(self.headers.get("Content-Length", 0))
        update = json.loads(self.rfile.read(length) or b"{}")
        msg = telegram.parse_update(update)
        if msg:
            reply = BOT.handle(msg)
            send_message(telegram.reply_payload(msg.chat_id, reply))
        self._json(200, {"ok": True})

    def _json(self, code: int, body: dict):
        data = json.dumps(body).encode()
        self.send_response(code)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def log_message(self, *args):  # quiet logs
        pass


if __name__ == "__main__":
    port = int(os.environ.get("PORT", "8080"))
    print(f"chat-bot webhook listening on :{port}")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
