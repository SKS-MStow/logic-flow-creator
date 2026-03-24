"""
Logic Flow Editor — Local dev server with auto-save support.

Serves static files and handles named flow sessions via:
  GET  /flows              — list all saved flows
  GET  /flows/<name>.json  — load a specific flow
  POST /save?flow=<name>   — save to a named flow (default: "untitled")

Each flow is stored as a JSON file in the logic-flows/ folder.

Usage:
    python logic-flow-server.py [port]
    Default port: 8000
    Opens: http://localhost:8000/logic-flow-editor.html
"""

import http.server
import json
import os
import re
import sys
import urllib.parse
import webbrowser
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
ROOT = Path(__file__).parent
FLOWS_DIR = ROOT / "logic-flows"
FLOWS_DIR.mkdir(exist_ok=True)


def safe_name(name):
    """Sanitize flow name to a safe filename."""
    name = re.sub(r'[^\w\-\s]', '', name).strip().replace(' ', '-').lower()
    return name or "untitled"


class FlowHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_GET(self):
        parsed = urllib.parse.urlparse(self.path)

        # List all flows
        if parsed.path == "/flows":
            flows = []
            for f in sorted(FLOWS_DIR.glob("*.json"), key=lambda p: p.stat().st_mtime, reverse=True):
                try:
                    data = json.loads(f.read_text(encoding="utf-8"))
                    node_count = len(data.get("nodes", []))
                    conn_count = len(data.get("connections", []))
                except Exception:
                    node_count = conn_count = 0
                flows.append({
                    "name": f.stem,
                    "file": f.name,
                    "modified": f.stat().st_mtime,
                    "nodes": node_count,
                    "connections": conn_count,
                })
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Cache-Control", "no-cache")
            self.end_headers()
            self.wfile.write(json.dumps(flows, indent=2).encode())
            return

        # Serve a specific flow file
        if parsed.path.startswith("/flows/") and parsed.path.endswith(".json"):
            name = parsed.path[7:-5]  # strip /flows/ and .json
            filepath = FLOWS_DIR / f"{safe_name(name)}.json"
            if filepath.exists():
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
                self.end_headers()
                self.wfile.write(filepath.read_bytes())
            else:
                self.send_response(404)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(b'{"error":"flow not found"}')
            return

        # Disable caching for the legacy data file too
        if "logic-flow-data.json" in parsed.path:
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")

        super().do_GET()

    def do_POST(self):
        parsed = urllib.parse.urlparse(self.path)

        if parsed.path == "/save":
            params = urllib.parse.parse_qs(parsed.query)
            flow_name = safe_name(params.get("flow", ["untitled"])[0])

            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                data = json.loads(body)
                filepath = FLOWS_DIR / f"{flow_name}.json"
                filepath.write_text(json.dumps(data, indent=2), encoding="utf-8")

                # Also write to legacy location for backwards compat
                legacy = ROOT / "logic-flow-data.json"
                legacy.write_text(json.dumps(data, indent=2), encoding="utf-8")

                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"ok": True, "file": str(filepath.name)}).encode())
            except json.JSONDecodeError as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())

        elif parsed.path == "/delete":
            params = urllib.parse.parse_qs(parsed.query)
            flow_name = safe_name(params.get("flow", [""])[0])
            if not flow_name:
                self.send_response(400)
                self.end_headers()
                return
            filepath = FLOWS_DIR / f"{flow_name}.json"
            if filepath.exists():
                filepath.unlink()
            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.end_headers()
            self.wfile.write(b'{"ok":true}')

        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def end_headers(self):
        self.send_header("Access-Control-Allow-Origin", "*")
        super().end_headers()

    def log_message(self, format, *args):
        msg = format % args
        if "POST" in msg or "404" in msg or "500" in msg or "/flows" in msg:
            print(f"  {msg}")


if __name__ == "__main__":
    server = http.server.HTTPServer(("", PORT), FlowHandler)
    url = f"http://localhost:{PORT}/logic-flow-editor.html"
    print(f"Logic Flow Editor server running on port {PORT}")
    print(f"  Editor:    {url}")
    print(f"  Flows dir: {FLOWS_DIR}")
    print(f"  API:")
    print(f"    GET  /flows              — list all saved flows")
    print(f"    GET  /flows/<name>.json  — load a specific flow")
    print(f"    POST /save?flow=<name>   — save a flow")
    print()
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
