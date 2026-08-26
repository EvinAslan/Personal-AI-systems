#!/usr/bin/env python3
"""
Desktop App Wrapper
Launches the Flask backend in a daemon thread and wraps the frontend
inside a native desktop window using pywebview.
"""

import threading
import time
import webview
from app import app

def start_flask():
    """Starts the Flask server in a separate background thread."""
    # We turn off debug and use_reloader to avoid double-spawning threads
    app.run(host="0.0.0.0", port=5000, debug=False, use_reloader=False)

if __name__ == '__main__':
    # 1. Start backend server thread
    print("Starting backend web server...")
    server_thread = threading.Thread(target=start_flask)
    server_thread.daemon = True
    server_thread.start()
    
    # 2. Wait briefly for backend server to bind to port 5000
    time.sleep(1.5)
    
    # 3. Create native desktop window
    print("Launching Desktop UI...")
    webview.create_window(
        title='Aether Calendar - Personal AI Assistant', 
        url='http://127.0.0.1:5000', 
        width=1280, 
        height=820,
        resizable=True,
        min_size=(800, 600)
    )
    
    # 4. Start the pywebview render loop
    webview.start()
