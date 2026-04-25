import json
from typing import AsyncGenerator

import httpx
import websockets


class NimbusClient:
    def __init__(self, backend: str):
        self.base_url = backend.rstrip("/")
        self.ws_base = self.base_url.replace("https://", "wss://").replace("http://", "ws://")

    async def get_or_create_workspace(self, name: str) -> dict:
        async with httpx.AsyncClient() as http:
            resp = await http.get(f"{self.base_url}/workspaces/")
            resp.raise_for_status()
            for ws in resp.json():
                if ws["name"] == name:
                    return ws
            resp = await http.post(f"{self.base_url}/workspaces/", json={"name": name})
            resp.raise_for_status()
            return resp.json()

    async def get_or_create_repo(self, workspace_id: str, url: str, name: str) -> dict:
        async with httpx.AsyncClient() as http:
            resp = await http.get(f"{self.base_url}/workspaces/{workspace_id}/repos")
            resp.raise_for_status()
            for repo in resp.json():
                if repo["url"] == url:
                    return repo
            resp = await http.post(
                f"{self.base_url}/repos/",
                json={"workspace_id": workspace_id, "url": url, "name": name},
            )
            resp.raise_for_status()
            return resp.json()

    async def create_task(self, workspace_id: str, repo_id: str, description: str) -> dict:
        async with httpx.AsyncClient() as http:
            resp = await http.post(
                f"{self.base_url}/tasks/",
                json={"workspace_id": workspace_id, "repo_id": repo_id, "description": description},
            )
            resp.raise_for_status()
            return resp.json()

    async def stream_task(self, task_id: str) -> AsyncGenerator[dict, None]:
        uri = f"{self.ws_base}/tasks/{task_id}/ws"
        async with websockets.connect(uri) as ws:
            async for raw in ws:
                yield json.loads(raw)
