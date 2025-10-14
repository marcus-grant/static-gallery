import os
import subprocess
import threading
import time
from pathlib import Path
from http.server import HTTPServer, SimpleHTTPRequestHandler
from urllib.parse import urlparse
import sys


class DevServer:
    def __init__(self, port=8000, directory="prod/site", reload=False):
        self.port = port
        self.directory = directory
        self.reload = reload
        self.server = None
        
    def handle_request(self, request):
        """Handle HTTP request and return response or 404"""
        path = request.path
        
        # Handle /gallery route
        if path == "/gallery":
            gallery_file = Path(self.directory) / "gallery.html"
            if gallery_file.exists():
                return "gallery.html"
            else:
                return 404
        
        # Handle other routes
        if path == "/":
            index_file = Path(self.directory) / "index.html"
            if index_file.exists():
                return "index.html"
            else:
                return 404
        
        # Check if file exists
        file_path = Path(self.directory) / path.lstrip('/')
        if file_path.exists() and file_path.is_file():
            return str(file_path.relative_to(self.directory))
        
        return 404
    
    def on_file_changed(self, file_path):
        """Handle file change event"""
        print(f"File changed: {file_path}")
        self.rebuild_site()
    
    def rebuild_site(self):
        """Rebuild the site using build command"""
        print("Rebuilding site...")
        result = subprocess.run([
            sys.executable, "manage.py", "build"
        ], capture_output=True, text=True)
        
        if result.returncode == 0:
            print("Site rebuilt successfully")
        else:
            print(f"Build failed: {result.stderr}")
    
    def start_server(self):
        """Start the HTTP server"""
        print(f"Serving from {self.directory} on port {self.port}")
        
        # Change to the directory we want to serve
        original_dir = os.getcwd()
        os.chdir(self.directory)
        
        try:
            handler = CustomHTTPRequestHandler
            handler.dev_server = self
            
            self.server = HTTPServer(('localhost', self.port), handler)
            self.server.serve_forever()
        finally:
            os.chdir(original_dir)
    
    def start(self):
        """Start the development server"""
        # Set up file watcher if reload is enabled
        if self.reload:
            self.setup_file_watcher()
        
        # Start the server
        self.start_server()
    
    def setup_file_watcher(self):
        """Set up file watching for auto-rebuild"""
        try:
            import watchdog
            from watchdog.observers import Observer
            from watchdog.events import FileSystemEventHandler
            
            class ChangeHandler(FileSystemEventHandler):
                def __init__(self, dev_server):
                    self.dev_server = dev_server
                
                def on_modified(self, event):
                    if not event.is_directory:
                        # Watch for template, CSS, JS changes
                        if any(ext in event.src_path for ext in ['.j2.html', '.css', '.js']):
                            self.dev_server.on_file_changed(event.src_path)
            
            observer = Observer()
            
            # Only watch directories that exist
            watch_dirs = ["src/template", "static"]
            for watch_dir in watch_dirs:
                if Path(watch_dir).exists():
                    observer.schedule(ChangeHandler(self), watch_dir, recursive=True)
                    print(f"Watching {watch_dir} for changes")
                else:
                    print(f"Warning: {watch_dir} not found, skipping watch")
            
            observer.start()
            print("File watcher started")
            
        except ImportError:
            print("Warning: watchdog not installed, hot reload disabled")


class CustomHTTPRequestHandler(SimpleHTTPRequestHandler):
    """Custom HTTP handler that implements routing logic"""
    
    def log_error(self, format, *args):
        # Suppress broken pipe errors in logs
        if "Broken pipe" in str(args):
            return
        super().log_error(format, *args)
    
    def do_GET(self):
        """Handle GET requests with custom routing"""
        # Handle /gallery route specifically
        if self.path == "/gallery":
            gallery_file = Path("gallery.html")
            if gallery_file.exists():
                self.path = "/gallery.html"
            else:
                self.send_error(404, "Gallery not found")
                return
        
        # Handle /photos/* routes - serve from prod/pics/
        elif self.path.startswith("/photos/"):
            # Map /photos/thumb/file.webp -> prod/pics/thumb/file.webp
            photo_path = self.path[8:]  # Remove "/photos/"
            actual_file = Path("..") / "pics" / photo_path
            
            if actual_file.exists():
                try:
                    # Serve the file directly
                    self.send_response(200)
                    if photo_path.endswith('.webp'):
                        self.send_header('Content-type', 'image/webp')
                    elif photo_path.endswith('.jpg'):
                        self.send_header('Content-type', 'image/jpeg')
                    self.end_headers()
                    
                    with open(actual_file, 'rb') as f:
                        self.wfile.write(f.read())
                    return
                except (BrokenPipeError, ConnectionResetError):
                    # Client disconnected, ignore
                    return
            else:
                self.send_error(404, f"Photo not found: {photo_path}")
                return
        
        # Handle root route
        elif self.path == "/":
            index_file = Path("index.html")
            if not index_file.exists():
                self.send_error(404, "No index.html found")
                return
        
        # Let SimpleHTTPRequestHandler handle the rest
        super().do_GET()