import datetime
import json
import os
import mimetypes
from http.server import BaseHTTPRequestHandler
from google import genai

class handler(BaseHTTPRequestHandler):
    def do_POST(self):
        if self.path.startswith('/api/token'):
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
        else:
            self.send_response(404)
            self.end_headers()

    def do_GET(self):
        path = self.path
        # Clean query parameters if any
        if '?' in path:
            path = path.split('?')[0]

        if path == '/' or path == '':
            path = '/index.html'

        # If User directly accesses /api/token via browser
        if path.startswith('/api/token'):
            self.send_response(200)
            self.send_header('Content-Type', 'text/html; charset=utf-8')
            self.end_headers()
            html = """
            <html>
                <body style="font-family: sans-serif; text-align: center; margin-top: 50px;">
                    <h1>API d'authentification fonctionnelle !</h1>
                    <p>Cette URL (<code>/api/token</code>) est destinée aux requêtes <b>POST</b>.</p>
                    <p>Pour lancer l'application, veuillez vous rendre sur la <a href="/">page d'accueil principale</a>.</p>
                </body>
            </html>
            """
            self.wfile.write(html.encode('utf-8'))
            return

        # Determine the physical path of the requested file inside frontend directory
        base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        frontend_dir = os.path.join(base_dir, 'frontend')
        
        # Remove leading slash for safe join
        safe_path = path.lstrip('/')
        file_path = os.path.join(frontend_dir, safe_path)
        
        # Prevent directory traversal
        if not os.path.abspath(file_path).startswith(os.path.abspath(frontend_dir)):
            self.send_response(403)
            self.end_headers()
            return

        if os.path.exists(file_path) and os.path.isfile(file_path):
            content_type, _ = mimetypes.guess_type(file_path)
            if not content_type:
                content_type = 'application/octet-stream'
                
            self.send_response(200)
            self.send_header('Content-Type', content_type)
            self.end_headers()
            
            with open(file_path, 'rb') as f:
                self.wfile.write(f.read())
        else:
            self.send_response(404)
            self.send_header('Content-Type', 'text/plain')
            self.end_headers()
            self.wfile.write(f"Vercel Serverless File not found: {path}".encode('utf-8'))

    def do_OPTIONS(self):
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'POST, GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
