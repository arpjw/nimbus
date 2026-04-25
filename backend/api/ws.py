import asyncio
import json
from collections import defaultdict

from fastapi import WebSocket
from starlette.websockets import WebSocketDisconnect


class ConnectionManager:
    def __init__(self):
        self._connections: dict[str, list[WebSocket]] = defaultdict(list)

    async def connect(self, task_id: str, ws: WebSocket):
        await ws.accept()
        self._connections[task_id].append(ws)

    def disconnect(self, task_id: str, ws: WebSocket):
        if ws in self._connections[task_id]:
            self._connections[task_id].remove(ws)

    async def broadcast(self, task_id: str, event: dict):
        message = json.dumps(event)
        dead = []
        for ws in self._connections.get(task_id, []):
            try:
                await ws.send_text(message)
            except Exception:
                dead.append(ws)
        for ws in dead:
            self.disconnect(task_id, ws)


manager = ConnectionManager()

task_queues: dict[str, asyncio.Queue] = {}


def get_or_create_queue(task_id: str) -> asyncio.Queue:
    if task_id not in task_queues:
        task_queues[task_id] = asyncio.Queue()
    return task_queues[task_id]


async def pump_queue_to_ws(task_id: str):
    queue = task_queues.get(task_id)
    if not queue:
        return
    while True:
        try:
            event = await asyncio.wait_for(queue.get(), timeout=1.0)
            await manager.broadcast(task_id, event)
            if event.get("phase") in ("done", "failed"):
                break
        except asyncio.TimeoutError:
            continue
        except Exception:
            break
