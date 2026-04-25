import json
from typing import AsyncGenerator

import httpx
import websockets


class NimbusClient:
    def __init__(self, backend: str, api_key: str | None = None):
        self.base_url = backend.rstrip("/")
        self.ws_base = self.base_url.replace("https://", "wss://").replace("http://", "ws://")
        self._headers = {"X-API-Key": api_key} if api_key else {}

    async def get_or_create_workspace(self, name: str) -> dict:
        async with httpx.AsyncClient(headers=self._headers) as http:
            resp = await http.get(f"{self.base_url}/workspaces/")
            resp.raise_for_status()
            for ws in resp.json():
                if ws["name"] == name:
                    return ws
            resp = await http.post(f"{self.base_url}/workspaces/", json={"name": name})
            resp.raise_for_status()
            return resp.json()

    async def get_or_create_repo(self, workspace_id: str, url: str, name: str) -> dict:
        async with httpx.AsyncClient(headers=self._headers) as http:
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

    async def create_task(
        self,
        workspace_id: str,
        repo_id: str,
        description: str,
        issue_number: int | None = None,
        repo_full_name: str | None = None,
    ) -> dict:
        payload: dict = {"workspace_id": workspace_id, "repo_id": repo_id, "description": description}
        if issue_number is not None:
            payload["issue_number"] = issue_number
        if repo_full_name is not None:
            payload["repo_full_name"] = repo_full_name
        async with httpx.AsyncClient(headers=self._headers) as http:
            resp = await http.post(f"{self.base_url}/tasks/", json=payload)
            resp.raise_for_status()
            return resp.json()

    async def approve_task(self, task_id: str) -> None:
        async with httpx.AsyncClient(headers=self._headers) as http:
            resp = await http.post(f"{self.base_url}/tasks/{task_id}/approve")
            resp.raise_for_status()

    async def reject_task(self, task_id: str) -> None:
        async with httpx.AsyncClient(headers=self._headers) as http:
            resp = await http.post(f"{self.base_url}/tasks/{task_id}/reject")
            resp.raise_for_status()

    async def approve_diff(self, task_id: str) -> None:
        async with httpx.AsyncClient(headers=self._headers) as http:
            resp = await http.post(f"{self.base_url}/tasks/{task_id}/approve-diff")
            resp.raise_for_status()

    async def reject_diff(self, task_id: str) -> None:
        async with httpx.AsyncClient(headers=self._headers) as http:
            resp = await http.post(f"{self.base_url}/tasks/{task_id}/reject-diff")
            resp.raise_for_status()

    async def review_pr(self, pr_url: str, post: bool = False) -> dict:
        async with httpx.AsyncClient(timeout=120.0) as http:
            resp = await http.post(
                f"{self.base_url}/review",
                json={"pr_url": pr_url, "post": post},
            )
            resp.raise_for_status()
            return resp.json()

    async def stream_task(self, task_id: str) -> AsyncGenerator[dict, None]:
        uri = f"{self.ws_base}/tasks/{task_id}/ws"
        extra_headers = list(self._headers.items()) if self._headers else None
        async with websockets.connect(uri, extra_headers=extra_headers) as ws:
            async for raw in ws:
                yield json.loads(raw)

    async def generate_tests_pr(self, repo_id: str, file_path: str) -> dict:
        async with httpx.AsyncClient(headers=self._headers, timeout=120.0) as http:
            resp = await http.post(
                f"{self.base_url}/generate-tests",
                json={"repo_id": repo_id, "file_path": file_path},
            )
            resp.raise_for_status()
            return resp.json()
