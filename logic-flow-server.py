"""
Logic Flow Editor — Local dev server with auto-save support.

Serves static files AND accepts POST /save to write logic-flow-data.json.
The editor auto-saves on every change, so Claude always sees the latest state.

Usage:
    python logic-flow-server.py [port]
    Default port: 8000
    Opens: http://localhost:8000/logic-flow-editor.html
"""

import http.server
import json
import os
import sys
import webbrowser
from pathlib import Path

PORT = int(sys.argv[1]) if len(sys.argv) > 1 else 8000
ROOT = Path(__file__).parent
DATA_FILE = ROOT / "logic-flow-data.json"


class FlowHandler(http.server.SimpleHTTPRequestHandler):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, directory=str(ROOT), **kwargs)

    def do_POST(self):
        if self.path == "/save":
            length = int(self.headers.get("Content-Length", 0))
            body = self.rfile.read(length)
            try:
                # Validate JSON before writing
                data = json.loads(body)
                DATA_FILE.write_text(json.dumps(data, indent=2), encoding="utf-8")
                self.send_response(200)
                self.send_header("Content-Type", "application/json")
                self.send_header("Access-Control-Allow-Origin", "*")
                self.end_headers()
                self.wfile.write(b'{"ok":true}')
            except json.JSONDecodeError as e:
                self.send_response(400)
                self.send_header("Content-Type", "application/json")
                self.end_headers()
                self.wfile.write(json.dumps({"error": str(e)}).encode())
        else:
            self.send_response(404)
            self.end_headers()

    def do_OPTIONS(self):
        # CORS preflight
        self.send_response(200)
        self.send_header("Access-Control-Allow-Origin", "*")
        self.send_header("Access-Control-Allow-Methods", "POST, GET, OPTIONS")
        self.send_header("Access-Control-Allow-Headers", "Content-Type")
        self.end_headers()

    def end_headers(self):
        # Add CORS to all responses
        self.send_header("Access-Control-Allow-Origin", "*")
        # Disable caching for JSON data file
        if self.path and "logic-flow-data.json" in self.path:
            self.send_header("Cache-Control", "no-cache, no-store, must-revalidate")
        super().end_headers()

    def log_message(self, format, *args):
        # Quiet logging — only show saves and errors
        msg = format % args
        if "POST" in msg or "404" in msg or "500" in msg:
            print(f"  {msg}")


if __name__ == "__main__":
    server = http.server.HTTPServer(("", PORT), FlowHandler)
    url = f"http://localhost:{PORT}/logic-flow-editor.html"
    print(f"Logic Flow Editor server running on port {PORT}")
    print(f"  Editor:    {url}")
    print(f"  Data file: {DATA_FILE}")
    print(f"  Auto-save: POST /save")
    print()
    webbrowser.open(url)
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        print("\nServer stopped.")
        server.server_close()
