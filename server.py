import base64
import json
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from urllib.parse import urlparse
from client import analyze_base64

ROOT = Path(__file__).resolve().parent

class Handler(BaseHTTPRequestHandler):
    def send_json(self, status, data):
        payload = json.dumps(data).encode("utf-8")
        self.send_response(status)
        self.send_header("Content-Type", "application/json; charset=utf-8")
        self.send_header("Content-Length", str(len(payload)))
        self.end_headers()
        self.wfile.write(payload)

    def send_file(self, path, content_type):
        data = path.read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", content_type)
        self.send_header("Content-Length", str(len(data)))
        self.end_headers()
        self.wfile.write(data)

    def do_GET(self):
        path = urlparse(self.path).path
        if path == "/":
            return self.send_file(ROOT / "index.html", "text/html; charset=utf-8")
        if path == "/style.css":
            return self.send_file(ROOT / "style.css", "text/css; charset=utf-8")
        self.send_json(404, {"error": "Not found."})

    def do_POST(self):
        path = urlparse(self.path).path
        if path != "/api/analyze-xray":
            return self.send_json(404, {"error": "Not found."})
        try:
            length = int(self.headers.get("Content-Length", "0"))
            raw = self.rfile.read(length)
            body = json.loads(raw.decode("utf-8"))
            api_key = body.get("apiKey")
            image_base64 = body.get("imageBase64")
            mime_type = body.get("mimeType")
            if not isinstance(api_key, str) or not api_key.strip():
                return self.send_json(400, {"error": "A Gemini API key is required. Enter your API key in MedAI first."})
            if not isinstance(image_base64, str) or not mime_type:
                return self.send_json(400, {"error": "An X-ray image is required."})
            result = analyze_base64(image_base64, mime_type, api_key.strip())
            return self.send_json(200, result)
        except json.JSONDecodeError:
            return self.send_json(400, {"error": "Invalid JSON request."})
        except Exception as error:
            return self.send_json(500, {"error": str(error) or "Analysis failed."})

    def log_message(self, format, *args):
        print(f"{self.address_string()} - {format % args}")

if __name__ == "__main__":
    server = ThreadingHTTPServer(("127.0.0.1", 8000), Handler)
    print("MedAI is running at http://127.0.0.1:8000")
    print("Press Ctrl+C to stop the server.")
    try:
        server.serve_forever()
    except KeyboardInterrupt:
        pass
    finally:
        server.server_close()
