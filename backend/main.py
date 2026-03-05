"""FastAPI backend for Base L2 Airdrop Farming Bot."""
import asyncio
import json
import secrets
from typing import AsyncGenerator

from fastapi import Depends, FastAPI, HTTPException, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import StreamingResponse

from backend.agent import agent
from backend.config import settings

app = FastAPI(title="Base Farming Bot", version="1.0.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ─── Auth ──────────────────────────────────────────────────────────────────────

def _require_api_key(request: Request) -> None:
    """Enforce API key on all non-health endpoints. Disabled if BOT_API_KEY is empty."""
    if not settings.BOT_API_KEY:
        return
    provided = request.headers.get("X-API-Key", "")
    if not secrets.compare_digest(provided, settings.BOT_API_KEY):
        raise HTTPException(status_code=401, detail="Invalid API key")


# ─── Health ────────────────────────────────────────────────────────────────────

@app.get("/health")
async def health() -> dict:
    return {"status": "ok", "simulation_mode": settings.SIMULATION_MODE}


# ─── Agent control ─────────────────────────────────────────────────────────────

@app.post("/api/agent/start", dependencies=[Depends(_require_api_key)])
async def start_agent() -> dict:
    return await agent.start()


@app.post("/api/agent/stop", dependencies=[Depends(_require_api_key)])
async def stop_agent() -> dict:
    return await agent.stop()


@app.post("/api/agent/resume", dependencies=[Depends(_require_api_key)])
async def resume_agent() -> dict:
    return await agent.resume()


@app.get("/api/status", dependencies=[Depends(_require_api_key)])
async def get_status() -> dict:
    return agent.get_status()


# ─── Strategy data ─────────────────────────────────────────────────────────────

@app.get("/api/positions", dependencies=[Depends(_require_api_key)])
async def get_positions() -> dict:
    return {
        "defi_positions": agent.defi.get_positions(),
        "nft_mints": agent.nft.get_mints(),
        "bridge_transactions": agent.bridge.get_transactions(),
    }


@app.get("/api/events", dependencies=[Depends(_require_api_key)])
async def get_events() -> dict:
    return {"events": list(agent.events)}


@app.get("/api/scheduler", dependencies=[Depends(_require_api_key)])
async def get_scheduler() -> dict:
    return agent.scheduler.get_stats()


# ─── SSE stream ────────────────────────────────────────────────────────────────

@app.get("/api/stream")
async def stream_events(request: Request) -> StreamingResponse:
    """Server-Sent Events stream with bounded queue (no memory leak)."""
    queue: asyncio.Queue = asyncio.Queue(maxsize=200)

    async def callback(event: dict) -> None:
        try:
            queue.put_nowait(event)
        except asyncio.QueueFull:
            # Drop oldest, insert newest
            try:
                queue.get_nowait()
            except asyncio.QueueEmpty:
                pass
            try:
                queue.put_nowait(event)
            except asyncio.QueueFull:
                pass

    agent.add_event_callback(callback)

    async def event_generator() -> AsyncGenerator[str, None]:
        try:
            while True:
                if await request.is_disconnected():
                    break
                try:
                    event = await asyncio.wait_for(queue.get(), timeout=30.0)
                    yield f"data: {json.dumps(event)}\n\n"
                except asyncio.TimeoutError:
                    # Keepalive ping
                    yield ": keepalive\n\n"
        finally:
            agent.remove_event_callback(callback)

    return StreamingResponse(event_generator(), media_type="text/event-stream")
