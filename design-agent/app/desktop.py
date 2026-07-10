from __future__ import annotations

import socket
import threading
from contextlib import closing

import uvicorn


def run_desktop() -> None:
    try:
        import webview
    except ModuleNotFoundError as exc:
        raise RuntimeError("Missing dependency pywebview. Run `pip install -r requirements.txt`.") from exc

    port = _available_port(8000)
    server = uvicorn.Server(
        uvicorn.Config(
            "app.web_routes:app",
            host="127.0.0.1",
            port=port,
            log_level="warning",
        )
    )
    thread = threading.Thread(target=server.run, daemon=True)
    thread.start()

    try:
        webview.create_window(
            "SpellTalker Design Agent",
            f"http://127.0.0.1:{port}",
            width=1280,
            height=860,
            min_size=(960, 640),
        )
        webview.start()
    finally:
        server.should_exit = True
        thread.join(timeout=3)


def _available_port(start: int) -> int:
    for port in range(start, start + 100):
        with closing(socket.socket(socket.AF_INET, socket.SOCK_STREAM)) as sock:
            sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            try:
                sock.bind(("127.0.0.1", port))
            except OSError:
                continue
            return port
    raise RuntimeError("No available local port found.")
