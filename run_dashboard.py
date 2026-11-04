"""
AutoForensic AI — Enterprise Web Dashboard Launcher
===================================================
Launches the FastAPI forensic analysis dashboard server and automatically
opens the interactive web interface in your default browser.

Usage:
    python run_dashboard.py
"""

import sys
import socket
import webbrowser
import threading
import time
from pathlib import Path

# Force UTF-8 encoding on Windows console
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

def find_available_port(start_port=8000, max_attempts=10):
    """Find an available TCP port starting from start_port."""
    for port in range(start_port, start_port + max_attempts):
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as s:
            if s.connect_ex(("127.0.0.1", port)) != 0:
                return port
    return start_port

def open_browser(url, delay=1.5):
    """Open default web browser after delay."""
    time.sleep(delay)
    try:
        webbrowser.open(url)
    except Exception as e:
        print(f"Could not open browser automatically: {e}")

def main():
    port = find_available_port(8000)
    url = f"http://localhost:{port}"

    print("=" * 70)
    print("  AutoForensic — Enterprise Digital Media Forensics & Damage Engine")
    print("  Automated Motor Claims Fraud Detection & Assessment Platform")
    print("=" * 70)
    print(f"\n  Claims Verification Server Starting...")
    print(f"  Access Portal: \033[1;36m{url}\033[0m")
    print(f"  Security Gateway: 5 Forensic Layers Active")
    print(f"  Damage Detection: YOLOv8-Seg & MiDaS Monocular Depth Active")
    print(f"  Actuarial Cost Engine: Active")
    print(f"\n  Press Ctrl+C to stop the server.\n")

    # Launch browser in a background thread
    threading.Thread(target=open_browser, args=(url,), daemon=True).start()

    # Start Uvicorn with auto-reload
    import uvicorn
    uvicorn.run(
        "web.app:app",
        host="0.0.0.0",
        port=port,
        reload=True,
        log_level="info",
    )

if __name__ == "__main__":
    main()
