import datetime
import json
import os
from http.server import BaseHTTPRequestHandler
from google import genai

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        try:
            api_key = os.environ.get("GEMINI_API_KEY")
            if not api_key:
                self.send_response(500)
                self.send_header('Content-Type', 'application/json')
                self.end_headers()
                self.wfile.write(json.dumps({"error": "GEMINI_API_KEY not configured"}).encode('utf-8'))
                return

            client = genai.Client(api_key=api_key, http_options={"api_version": "v1alpha"})
            
            now = datetime.datetime.now(tz=datetime.timezone.utc)
            expire_time = now + datetime.timedelta(minutes=30)
            
            token = client.auth_tokens.create(
                config={
                    "uses": 1,
                    "expire_time": expire_time.isoformat(),
                    "new_session_expire_time": (now + datetime.timedelta(minutes=1)).isoformat(),
                    "http_options": {"api_version": "v1alpha"},
                }
            )
            
            response_data = {
                "token": token.name,
                "expires_at": expire_time.isoformat()
            }
            
            self.send_response(200)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            self.wfile.write(json.dumps(response_data).encode('utf-8'))
            
        except Exception as e:
            print(f"Error generating ephemeral token: {e}")
            self.send_response(500)
            self.send_header('Content-Type', 'application/json')
            self.end_headers()
            error_data = {"error": str(e)}
            self.wfile.write(json.dumps(error_data).encode('utf-8'))

    def do_OPTIONS(self):
        # Allow CORS for direct testing, though Vercel handles same-domain natively
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
