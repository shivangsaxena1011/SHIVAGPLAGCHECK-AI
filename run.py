"""
SHIVANG PLAGCHECK AI - Unified Local PC Runner
Starts both the FastAPI Backend and Next.js Frontend together on a single server (http://localhost:8000).
"""

from __future__ import annotations

import os
import sys
import time
import subprocess
import threading
import webbrowser
from pathlib import Path

# Safe encoding handling on Windows
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

ROOT_DIR = Path(__file__).resolve().parent
FRONTEND_DIR = ROOT_DIR / "frontend"
FRONTEND_OUT = FRONTEND_DIR / "out"


def ensure_frontend_built() -> None:
    """Ensure the static frontend is compiled before launching."""
    if not (FRONTEND_OUT / "index.html").exists():
        print("[+] Compiling frontend static bundle for unified serving...")
        try:
            subprocess.run(["npm", "run", "build"], cwd=str(FRONTEND_DIR), check=True, shell=True)
            print("[OK] Frontend successfully compiled!\n")
        except Exception as err:
            print(f"[!] Warning: Could not compile frontend automatically: {err}")
            print("You can build it manually by running: cd frontend && npm run build\n")
    else:
        print("[OK] Frontend production build detected at frontend/out")


def open_browser(url: str, delay: float = 2.5) -> None:
    """Open default web browser after server starts."""
    time.sleep(delay)
    print(f"[>] Opening web browser at {url} ...")
    webbrowser.open(url)


def main() -> None:
    # Ensure root and backend dirs are on sys.path
    if str(ROOT_DIR) not in sys.path:
        sys.path.insert(0, str(ROOT_DIR))
    if str(ROOT_DIR / "backend") not in sys.path:
        sys.path.insert(0, str(ROOT_DIR / "backend"))

    print("=" * 68)
    print("           SHIVANG PLAGCHECK AI - UNIFIED LOCAL SERVER")
    print("=" * 68)
    print("  Host:       http://localhost:8000")
    print("  Web UI:     http://localhost:8000/")
    print("  API Docs:   http://localhost:8000/docs")
    print("  Health:     http://localhost:8000/health")
    print("  Status:     Frontend + Backend unified on ONE server (100% Free)")
    print("=" * 68)

    ensure_frontend_built()

    # Launch browser opener in background thread
    threading.Thread(target=open_browser, args=("http://localhost:8000", 2.5), daemon=True).start()

    import uvicorn

    try:
        uvicorn.run(
            "backend.app.main:app",
            host="0.0.0.0",
            port=8000,
            log_level="info",
            reload=False,
        )
    except KeyboardInterrupt:
        print("\n[!] SHIVANG PLAGCHECK AI server stopped safely. Goodbye!")


if __name__ == "__main__":
    main()
