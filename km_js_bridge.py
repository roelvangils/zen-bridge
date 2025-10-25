#!/usr/bin/env python3
from http.server import BaseHTTPRequestHandler, HTTPServer
import json, urllib.parse, threading, time

HOST, PORT = "127.0.0.1", 8765

store_lock = threading.Lock()
pending_code = None    # laatste te leveren code
last_result = None     # laatste resultaat

def cors_headers(handler):
    handler.send_header("Access-Control-Allow-Origin", "http://127.0.0.1:8765")
    handler.send_header("Access-Control-Allow-Origin", "*")
    handler.send_header("Access-Control-Allow-Methods", "GET, POST, OPTIONS")
    handler.send_header("Access-Control-Allow-Headers", "Content-Type")

class Handler(BaseHTTPRequestHandler):
    def _send_json(self, obj, code=200):
        self.send_response(code)
        cors_headers(self)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.end_headers()
        self.wfile.write(json.dumps(obj).encode("utf-8"))

    def do_OPTIONS(self):
        self.send_response(204)
        cors_headers(self)
        self.end_headers()

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/health":
            self._send_json({"ok": True, "ts": time.time()})
            return
        if parsed.path == "/next":
            # Eenmalig uitleveren en dan leegmaken
            global pending_code
            with store_lock:
                code = pending_code
                pending_code = None
            if code:
                self._send_json({"code": code})
            else:
                # leeg antwoord = niets te doen
                self.send_response(204)
                cors_headers(self)
                self.end_headers()
            return
        if parsed.path == "/last_result":
            global last_result
            with store_lock:
                res = last_result
            self._send_json(res if res is not None else {"ok": False, "error": "no result yet"})
            return

        self.send_response(404)
        self.end_headers()

    def do_POST(self):
        length = int(self.headers.get("Content-Length", "0"))
        raw = self.rfile.read(length) if length else b""
        try:
            data = json.loads(raw.decode("utf-8") or "{}")
        except Exception:
            data = {}

        parsed = urllib.parse.urlparse(self.path)
        if parsed.path == "/run":
            code = data.get("code", "")
            if not isinstance(code, str) or not code.strip():
                self._send_json({"ok": False, "error": "missing code"}, 400)
                return
            global pending_code
            with store_lock:
                pending_code = code
            self._send_json({"ok": True})
            return

        if parsed.path == "/result":
            global last_result
            with store_lock:
                last_result = data
            self._send_json({"ok": True})
            return

        self.send_response(404)
        self.end_headers()

def main():
    httpd = HTTPServer((HOST, PORT), Handler)
    print(f"KM JS Bridge listening on http://{HOST}:{PORT}")
    httpd.serve_forever()

if __name__ == "__main__":
    main()
