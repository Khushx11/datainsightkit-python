"""Serve the local browser interface."""
import argparse
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path

ASSETS = Path(__file__).with_name("web_assets")
FILES = {
    "/": ("index.html", "text/html"),
    "/style.css": ("style.css", "text/css"),
    "/app.js": ("app.js", "text/javascript"),
    "/sample.csv": ("sample.csv", "text/csv"),
}

def serve(port, endpoint, process, limit, state=None):
    class Handler(BaseHTTPRequestHandler):
        def send(self, status, kind, content):
            self.send_response(status)
            self.send_header("Content-Type", kind + "; charset=utf-8")
            self.send_header("Content-Length", str(len(content)))
            self.send_header("Cache-Control", "no-store")
            self.send_header("X-Content-Type-Options", "nosniff")
            self.send_header("Content-Security-Policy", "default-src 'self'; frame-ancestors 'none'")
            self.end_headers()
            self.wfile.write(content)

        def send_json(self, status, value):
            self.send(status, "application/json", json.dumps(value, allow_nan=False).encode())

        def do_GET(self):
            if self.path == "/api/session" and state is not None:
                self.send_json(200, state)
                return
            if self.path not in FILES:
                self.send_error(404)
                return
            name, kind = FILES[self.path]
            self.send(200, kind, (ASSETS / name).read_bytes())

        def do_POST(self):
            if self.path != endpoint:
                self.send_error(404)
                return
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://127.0.0.1:{port}", f"http://localhost:{port}"}:
                self.send_error(403)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                if not 0 < length <= limit:
                    self.send_json(413, {"error": "Request exceeds the input limit or is empty."})
                    return
                body = self.rfile.read(length).decode("utf-8-sig")
                self.send_json(200, process(body))
            except (ValueError, OverflowError) as error:
                self.send_json(400, {"error": str(error)})

    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        print(f"Open http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

from io import StringIO
from .ingest import read_stream
from .report import analyse

def profile_csv(body):
    headers, rows = read_stream(StringIO(body, newline=""), max_rows=10000, max_columns=40)
    return analyse(headers, rows)

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    serve(args.port, "/api/profile", profile_csv, 1024 * 1024)

if __name__ == "__main__":
    main()
