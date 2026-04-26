"""Broadcast Discord moderation events to connected WebSocket clients (FastAPI loop)."""

from __future__ import annotations

import asyncio
import json
import threading
from typing import Any, Optional

from starlette.websockets import WebSocket

_main_loop: Optional[asyncio.AbstractEventLoop] = None
_clients: set[WebSocket] = set()
_lock = threading.Lock()
_warned_no_loop = False


def set_main_loop(loop: asyncio.AbstractEventLoop) -> None:
    global _main_loop
    _main_loop = loop


async def register(ws: WebSocket) -> None:
    with _lock:
        _clients.add(ws)


async def unregister(ws: WebSocket) -> None:
    with _lock:
        _clients.discard(ws)


async def _broadcast_raw(data: str) -> None:
    dead: list[WebSocket] = []
    with _lock:
        clients = list(_clients)
    for ws in clients:
        try:
            await ws.send_text(data)
        except Exception:
            dead.append(ws)
    for ws in dead:
        await unregister(ws)


def broadcast_event(event: dict[str, Any]) -> None:
    """Safe to call from the Discord bot thread."""
    global _warned_no_loop
    loop = _main_loop
    if loop is None or not loop.is_running():
        if not _warned_no_loop:
            _warned_no_loop = True
            print(
                "[live_hub] broadcast skipped: FastAPI event loop not ready — "
                "live WebSocket clients will miss pushes until the server finishes startup."
            )
        return
    payload = json.dumps(event, default=str)
    try:
        asyncio.run_coroutine_threadsafe(_broadcast_raw(payload), loop)
    except RuntimeError:
        pass
