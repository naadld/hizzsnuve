import os
import sys
import json
import subprocess
import threading
from http.server import HTTPServer, BaseHTTPRequestHandler

PORT = 8888
AUTH_TOKEN = "HLHana@292710$"
PROJECT_ROOT = "/media/vpsg16gb/HaRiDisk/Youtube/historysnooze"

class VPSWebhookHandler(BaseHTTPRequestHandler):
    def log_message(self, format, *args):
        print(f"[VPS Daemon] {self.address_string()} - {args[0]}")

    def do_POST(self):
        auth_header = self.headers.get("x-vps-auth")
        if auth_header != AUTH_TOKEN:
            self.send_response(401)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(b'{"error": "Unauthorized"}')
            return

        content_length = int(self.headers.get('Content-Length', 0))
        post_data = self.rfile.read(content_length).decode('utf-8')
        data = json.loads(post_data) if post_data else {}

        if self.path in ["/run-imagefx", "/api/run-imagefx"]:
            character = data.get("character", "Marcus_Aurelius")
            project_dir = data.get("project_dir", f"01.Projects/{character}")

            print(f"🚀 [DIRECT TRIGGER FROM CLOUDFLARE] Spawning ImageFX for '{character}' on VPS...")

            def run_job():
                cmd = [
                    sys.executable,
                    os.path.join(PROJECT_ROOT, "00.System/01.Scripts/imagefx_vps_runner.py"),
                    "--character", character,
                    "--project_dir", project_dir
                ]
                try:
                    subprocess.run(cmd, cwd=PROJECT_ROOT)
                except Exception as e:
                    print(f"⛔ Error running imagefx_vps_runner: {e}")

            threading.Thread(target=run_job, daemon=True).start()

            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps({
                "status": "STARTED",
                "character": character,
                "target": "VPS_PLAYWRIGHT_CHROME_CDP",
                "message": f"🚀 Successfully launched ImageFX Playwright Runner directly on VPS for '{character}'!"
            }).encode('utf-8'))
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        self.send_response(200)
        self.send_header('Content-Type', 'application/json')
        self.end_headers()
        self.wfile.write(b'{"status": "ONLINE", "service": "HistorySnooze VPS Direct Automation Daemon", "port": 8888}')

def run_server():
    server = HTTPServer(("0.0.0.0", PORT), VPSWebhookHandler)
    print(f"📡 HistorySnooze VPS Direct Webhook Daemon running on port {PORT}...")
    server.serve_forever()

if __name__ == "__main__":
    run_server()
