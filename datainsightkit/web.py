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
}

def serve(port):
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
            if self.path == "/api/sample":
                self.send_json(200, sample_report())
                return
            if self.path not in FILES:
                self.send_error(404)
                return
            name, kind = FILES[self.path]
            self.send(200, kind, (ASSETS / name).read_bytes())

        def do_POST(self):
            if self.path != "/api/profile":
                self.send_error(404)
                return
            origin = self.headers.get("Origin")
            if origin and origin not in {f"http://127.0.0.1:{self.server.server_port}", f"http://localhost:{self.server.server_port}"}:
                self.send_error(403)
                return
            try:
                length = int(self.headers.get("Content-Length", "0"))
                structured = self.headers.get_content_type() == "application/json"
                limit = MAX_BYTES * 6 + 65536 if structured else MAX_BYTES
                if not 0 < length <= limit:
                    self.send_json(413, {"error": "Request exceeds the input limit or is empty."})
                    return
                body = self.rfile.read(length).decode("utf-8-sig")
                if structured:
                    payload = json.loads(body)
                    if not isinstance(payload, dict):
                        raise ValueError("Profile request must be an object.")
                    body = payload.get("csv")
                    categorical = payload.get("categorical", [])
                    if not isinstance(body, str) or not isinstance(categorical, list) or any(
                        not isinstance(name, str) for name in categorical
                    ):
                        raise ValueError("Supply CSV text and a list of categorical column names.")
                    if len(body.encode("utf-8")) > MAX_BYTES:
                        self.send_json(413, {"error": "CSV exceeds the 2 MiB limit."})
                        return
                else:
                    categorical = ()
                self.send_json(200, profile_csv(body, categorical=categorical))
            except (ValueError, OverflowError) as error:
                self.send_json(400, {"error": str(error)})

    with ThreadingHTTPServer(("127.0.0.1", port), Handler) as server:
        print(f"Open http://127.0.0.1:{server.server_port}", flush=True)
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            pass

from collections import Counter
from functools import lru_cache
from io import StringIO
from .ingest import read_stream
from .report import analyse

MAX_BYTES = 2 * 1024 * 1024
MAX_ROWS = 15000
SHOPPER_CATEGORIES = {
    "Month", "OperatingSystems", "Browser", "Region", "TrafficType", "VisitorType",
    "Weekend", "Revenue",
}
SHOPPER_SOURCE = "https://doi.org/10.24432/C5F88Q"


def profile_csv(body, *, categorical=()):
    headers, rows = read_stream(StringIO(body, newline=""), max_rows=MAX_ROWS, max_columns=40)
    return analyse(headers, rows, categorical=categorical)


@lru_cache(maxsize=1)
def sample_report():
    headers, rows = read_stream(
        StringIO((ASSETS / "sample.csv").read_text(encoding="utf-8"), newline="")
    )
    report = analyse(headers, rows, categorical=SHOPPER_CATEGORIES)
    sessions = Counter(row["VisitorType"] for row in rows)
    purchases = Counter(row["VisitorType"] for row in rows if row["Revenue"] == "TRUE")
    report["source"] = {"name": "UCI Online Shoppers", "url": SHOPPER_SOURCE}
    report["case_study"] = {
        "purchases": sum(purchases.values()),
        "segments": [
            {"name": label.replace("_", " "), "sessions": count,
             "purchases": purchases[label], "rate": purchases[label] / count}
            for label, count in sessions.most_common()
        ],
    }
    return report

def main():
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument("--port", type=int, default=8000)
    args = parser.parse_args()
    serve(args.port)

if __name__ == "__main__":
    main()
