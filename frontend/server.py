#!/usr/bin/env python3
"""
Frontend Server for Healthcare AI Assistant
Serves HTML, CSS, and JavaScript files with correct MIME types
"""

import http.server
import socketserver
import os
import mimetypes
from pathlib import Path
from urllib.parse import urlparse

# Configure MIME types
mimetypes.init()
mimetypes.add_type('text/css', '.css')
mimetypes.add_type('application/javascript', '.js')
mimetypes.add_type('text/html', '.html')

class FrontendHandler(http.server.SimpleHTTPRequestHandler):
    """Custom HTTP request handler for frontend server"""
    
    def end_headers(self):
        """Add caching and CORS headers"""
        # Add CORS headers
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        
        # Add cache control for static assets
        if self.path.endswith('.css') or self.path.endswith('.js'):
            self.send_header('Cache-Control', 'public, max-age=3600')
        elif self.path.endswith('.html'):
            self.send_header('Cache-Control', 'no-cache, must-revalidate')
        
        # Set correct content-type for CSS
        if self.path.endswith('.css'):
            self.send_header('Content-Type', 'text/css; charset=utf-8')
        elif self.path.endswith('.js'):
            self.send_header('Content-Type', 'application/javascript; charset=utf-8')
        elif self.path.endswith('.html'):
            self.send_header('Content-Type', 'text/html; charset=utf-8')
        
        super().end_headers()
    
    def do_GET(self):
        """Handle GET requests"""
        # Route all HTML file requests to index.html (SPA routing)
        path = urlparse(self.path).path
        
        # Log request
        print(f"GET {path}")
        
        # Serve files normally
        return super().do_GET()
    
    def do_OPTIONS(self):
        """Handle OPTIONS requests (CORS preflight)"""
        self.send_response(200)
        self.send_header('Access-Control-Allow-Origin', '*')
        self.send_header('Access-Control-Allow-Methods', 'GET, OPTIONS')
        self.send_header('Access-Control-Allow-Headers', 'Content-Type')
        self.end_headers()
    
    def log_message(self, format, *args):
        """Custom logging"""
        print(f"[{self.client_address[0]}] {format % args}")


def run_server(port=8080, host='0.0.0.0'):
    """Run the frontend server"""
    
    # Change to frontend directory
    frontend_dir = os.path.dirname(os.path.abspath(__file__))
    os.chdir(frontend_dir)
    
    print(f"\n{'='*60}")
    print(f"Healthcare AI Assistant - Frontend Server")
    print(f"{'='*60}")
    print(f"Serving directory: {frontend_dir}")
    print(f"Server URL: http://localhost:{port}")
    print(f"Press Ctrl+C to stop the server")
    print(f"{'='*60}\n")
    
    try:
        with socketserver.TCPServer((host, port), FrontendHandler) as httpd:
            print(f"✅ Server started on http://localhost:{port}")
            print(f"✅ CSS files serving from: {frontend_dir}/css/\n")
            httpd.serve_forever()
    except KeyboardInterrupt:
        print("\n\n❌ Server stopped.")
    except OSError as e:
        if "Address already in use" in str(e):
            print(f"❌ Error: Port {port} is already in use!")
            print(f"   Try running: netstat -ano | findstr :{port}")
        else:
            print(f"❌ Error: {e}")


if __name__ == '__main__':
    import sys
    port = int(sys.argv[1]) if len(sys.argv) > 1 else 8080
    run_server(port=port)
