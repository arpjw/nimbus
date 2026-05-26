from __future__ import annotations

import asyncio
import json

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect

from agent.orchestrator import _TASK_EVENTS_PREFIX, _TASK_HISTORY_PREFIX


class ConnectionManager:
    async def connect(self, task_id: str, ws: WebSocket) -> None:
        await ws.accept()

    async def broadcast(self, task_id: str, event: dict) -> None:
        from redis_client import get_redis
        redis_client = await get_redis()
        payload = json.dumps(event)
        channel = f"{_TASK_EVENTS_PREFIX}{task_id}"
        history_key = f"{_TASK_HISTORY_PREFIX}{task_id}"
        await redis_client.publish(channel, payload)
        await redis_client.rpush(history_key, payload)
        await redis_client.expire(history_key, 3600)


manager = ConnectionManager()


async def stream_task_events_to_ws(task_id: str, ws: WebSocket) -> None:
    from redis_client import get_redis

    redis_client = await get_redis()
    terminal_phases = {"done", "failed"}

    history = await redis_client.lrange(f"{_TASK_HISTORY_PREFIX}{task_id}", 0, -1)
    for event_bytes in history:
        data = event_bytes.decode() if isinstance(event_bytes, bytes) else event_bytes
        try:
            await ws.send_text(data)
        except Exception:
            return

    if history:
        last_raw = history[-1]
        last = json.loads(last_raw.decode() if isinstance(last_raw, bytes) else last_raw)
        if last.get("phase") in terminal_phases:
            return

    pubsub = redis_client.pubsub()
    await pubsub.subscribe(f"{_TASK_EVENTS_PREFIX}{task_id}")

    done_evt = asyncio.Event()

    async def _redis_to_ws() -> None:
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    raw = message["data"]
                    data = raw.decode() if isinstance(raw, bytes) else raw
                    try:
                        await ws.send_text(data)
                    except Exception:
                        done_evt.set()
                        return
                    parsed = json.loads(data)
                    if parsed.get("phase") in terminal_phases:
                        done_evt.set()
                        return
        except Exception:
            done_evt.set()

    async def _keep_alive() -> None:
        try:
            while not done_evt.is_set():
                try:
                    await asyncio.wait_for(ws.receive_text(), timeout=25)
                except asyncio.TimeoutError:
                    pass
                except (WebSocketDisconnect, Exception):
                    done_evt.set()
                    return
        except Exception:
            done_evt.set()

    redis_task = asyncio.create_task(_redis_to_ws())
    keepalive_task = asyncio.create_task(_keep_alive())

    await done_evt.wait()

    redis_task.cancel()
    keepalive_task.cancel()
    try:
        await asyncio.gather(redis_task, keepalive_task, return_exceptions=True)
    except Exception:
        pass
    finally:
        await pubsub.unsubscribe(f"{_TASK_EVENTS_PREFIX}{task_id}")
        await pubsub.aclose()
