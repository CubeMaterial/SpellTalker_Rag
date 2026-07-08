from __future__ import annotations

import uvicorn


def run_web() -> None:
    uvicorn.run(
        "app.web_routes:app",
        host="127.0.0.1",
        port=8000,
        reload=True,
    )

