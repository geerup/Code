"""Demo observability server: generates synthetic traffic, records metrics, and
exposes them at /metrics (Prometheus text), /metrics.json, and a live dashboard
at / (served from web/).

    python server.py        # http://localhost:8080
"""
from __future__ import annotations

import json
import os
import random
import threading
import time
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from metrics import Registry

REG = Registry()
REQS = REG.counter("http_requests_total")
ERRS = REG.counter("http_errors_total")
INFLIGHT = REG.gauge("in_flight_requests")
LAT = REG.histogram("request_latency_ms")


def synthetic_traffic() -> None:
    """Pretend to serve requests so the dashboard has something to show."""
    while True:
        INFLIGHT.inc()
        REQS.inc()
        latency = random.lognormvariate(3.5, 0.6)  # skewed, like real latency
        LAT.observe(latency)
        if random.random() < 0.05:
            ERRS.inc()
        time.sleep(0.05)
        INFLIGHT.dec()


class Handler(BaseHTTPRequestHandler):
    def do_GET(self):  # noqa: N802
        if self.path == "/metrics":
            self._respond(200, "text/plain; version=0.0.4", REG.render_prometheus().encode())
        elif self.path == "/metrics.json":
            self._respond(200, "application/json", json.dumps(REG.to_json()).encode())
        else:
            path = "web/index.html" if self.path in ("/", "") else "web" + self.path
            try:
                with open(path, "rb") as f:
                    self._respond(200, _ctype(path), f.read())
            except OSError:
                self._respond(404, "text/plain", b"not found")

    def _respond(self, code, ctype, body):
        self.send_response(code)
        self.send_header("Content-Type", ctype)
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    def log_message(self, *args):  # quiet
        pass


def _ctype(path: str) -> str:
    if path.endswith(".html"):
        return "text/html"
    if path.endswith(".js"):
        return "text/javascript"
    return "application/octet-stream"


if __name__ == "__main__":
    threading.Thread(target=synthetic_traffic, daemon=True).start()
    port = int(os.environ.get("PORT", "8080"))
    print(f"observability demo on :{port} (/metrics, /metrics.json, /)")
    ThreadingHTTPServer(("0.0.0.0", port), Handler).serve_forever()
