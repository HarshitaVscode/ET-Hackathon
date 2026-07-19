"""Vayu-Drishti — Unified Backend Entry Point.

Start with:  python -m backend.main
Or:         uvicorn backend.src.app:app --reload
"""

from __future__ import annotations

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(
        "backend.src.app:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info",
    )
