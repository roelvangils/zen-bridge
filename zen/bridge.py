#!/usr/bin/env python3
"""
Improved bridge server with request/response matching.
"""
from http.server import BaseHTTPRequestHandler, HTTPServer
import json
import urllib.parse
import threading
import time
import uuid
from typing import Dict, Optional, Any

HOST = "127.0.0.1"
PORT = 8765

# Thread-safe storage
store_lock = threading.Lock()
pending_requests: Dict[str, Dict[str, Any]] = {}
completed_requests: Dict[str, Dict[str, Any]] = {}

# Cleanup old requests after 5 minutes
MAX_REQUEST_AGE = 300


def cleanup_old_requests():
    """Remove requests older than MAX_REQUEST_AGE seconds."""
    now = time.time()
    with store_lock:
        expired = [
            req_id for req_id, req in pending_requests.items()
            if now - req['timestamp'] > MAX_REQUEST_AGE
        ]
        for req_id in expired:
            del pending_requests[req_id]

        expired = [
            req_id for req_id, req in completed_requests.items()
            if now - req['timestamp'] > MAX_REQUEST_AGE
        ]
        for req_id in expired:
            del completed_requests[req_id]


def cors_headers(handler):
    """Add CORS headers to allow browser access."""
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")


class BridgeHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        """Suppress default logging."""
        pass

    def _send_json(self, obj, code=200):
        """Send JSON response."""
        self.send_response(code)
        cors_headers(self)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

    def do_OPTIONS(self):
        """Handle CORS preflight."""
        self.send_response(204)
        cors_headers(self)
        self.end_headers()

    def do_GET(self):
        """Handle GET requests."""
        parsed = urllib.parse.urlparse(self.path)

        # Health check
        if parsed.path == "/health":
            cleanup_old_requests()
            with store_lock:
                self._send_json({
                    "ok": True,
                    "timestamp": time.time(),
                    "pending": len(pending_requests),
                    "completed": len(completed_requests)
                })
            return

        # Browser polls for next code to execute
        if parsed.path == "/next":
            cleanup_old_requests()
            with store_lock:
                # Get oldest pending request
                if pending_requests:
                    req_id = min(pending_requests.keys(),
                               key=lambda k: pending_requests[k]['timestamp'])
                    req = pending_requests[req_id]
                    self._send_json({
                        "request_id": req_id,
                        "code": req['code']
                    })
                    return

            # No pending requests
            self.send_response(204)
            cors_headers(self)
            self.end_headers()
            return

        # CLI polls for result of specific request
        if parsed.path == "/result":
            query = urllib.parse.parse_qs(parsed.query)
            request_id = query.get('request_id', [None])[0]

            if not request_id:
                self._send_json({"ok": False, "error": "missing request_id"}, 400)
                return

            with store_lock:
                if request_id in completed_requests:
                    result = completed_requests[request_id]
                    self._send_json(result)
                    return
                elif request_id in pending_requests:
                    self._send_json({"ok": False, "status": "pending"})
                    return
                else:
                    self._send_json({"ok": False, "error": "unknown request_id"}, 404)
                    return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        """Handle POST requests."""
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            data = {}

        parsed = urllib.parse.urlparse(self.path)

        # CLI submits code to run
        if parsed.path == "/run":
            code = data.get("code", "")
            if not isinstance(code, str) or not code.strip():
                self._send_json({"ok": False, "error": "missing code"}, 400)
                return

            request_id = str(uuid.uuid4())
            with store_lock:
                pending_requests[request_id] = {
                    "code": code,
                    "timestamp": time.time()
                }

            self._send_json({"ok": True, "request_id": request_id})
            return

        # Browser submits result
        if parsed.path == "/submit":
            request_id = data.get("request_id")
            if not request_id:
                self._send_json({"ok": False, "error": "missing request_id"}, 400)
                return

            with store_lock:
                if request_id in pending_requests:
                    del pending_requests[request_id]

                completed_requests[request_id] = {
                    "ok": data.get("ok", False),
                    "result": data.get("result"),
                    "error": data.get("error"),
                    "url": data.get("url"),
                    "title": data.get("title"),
                    "timestamp": time.time()
                }

            self._send_json({"ok": True})
            return

        self.send_response(404)
        self.end_headers()


def start_server(host: str = HOST, port: int = PORT, quiet: bool = False):
    """Start the bridge server."""
    httpd = HTTPServer((host, port), BridgeHandler)
    if not quiet:
        print(f"Zen Bridge server running on http://{host}:{port}")
    try:
        httpd.serve_forever()
    except KeyboardInterrupt:
        if not quiet:
            print("\nServer stopped")


if __name__ == "__main__":
    start_server()
