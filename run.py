"""Start the web server (and later the Huey worker thread) with one command."""

from __future__ import annotations

import threading
import time
import webbrowser

import uvicorn

from app.config import get_settings


def _open_browser(url: str, delay: float = 1.2) -> None:
    def _open() -> None:
        time.sleep(delay)
        try:
            webbrowser.open(url)
        except Exception:
            pass

    threading.Thread(target=_open, daemon=True).start()


def main() -> None:
    settings = get_settings()
    url = f"http://{settings.host}:{settings.port}"
    if settings.open_browser:
        _open_browser(url)
    print(f"Starting {settings.app_name}")
    print(f"Open {url} in your browser")
    print("Press Ctrl+C to stop")
    # Worker thread placeholder for Huey (Phase 3+)
    uvicorn.run(
        "app.main:app",
        host=settings.host,
        port=settings.port,
        reload=False,
        log_level="info",
    )


if __name__ == "__main__":
    main()
