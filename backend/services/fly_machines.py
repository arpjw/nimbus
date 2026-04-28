"""
Fly.io Machines API client.
Spins up and destroys nimbus-ide containers on demand.
"""

import os
import httpx
from typing import Optional

FLY_API_TOKEN = os.environ.get("FLY_API_TOKEN", "")
FLY_APP_NAME = os.environ.get("FLY_APP_NAME", "nimbus-ide")
FLY_API_BASE = "https://api.machines.dev/v1"
IDE_IMAGE = os.environ.get("IDE_IMAGE", "registry.fly.io/nimbus-ide:deployment-01KQ8QX521887QVWE7C913T2Z6")


def _headers() -> dict:
    return {
        "Authorization": f"Bearer {FLY_API_TOKEN}",
        "Content-Type": "application/json",
    }


async def create_machine(
    session_id: str,
    anthropic_api_key: str = "",
    voyage_api_key: str = "",
) -> dict:
    """
    Spin up a new Fly Machine for an IDE session.
    Returns machine info including the machine ID and private IP.
    """
    async with httpx.AsyncClient(timeout=30) as client:
        payload = {
            "name": f"nimbus-ide-{session_id[:8]}",
            "config": {
                "image": IDE_IMAGE,
                "env": {
                    "ANTHROPIC_API_KEY": anthropic_api_key or os.environ.get("ANTHROPIC_API_KEY", ""),
                    "VOYAGE_API_KEY": voyage_api_key or os.environ.get("VOYAGE_API_KEY", ""),
                    "SESSION_ID": session_id,
                },
                "services": [
                    {
                        "ports": [
                            {"port": 443, "handlers": ["tls", "http"]},
                            {"port": 80, "handlers": ["http"]},
                        ],
                        "protocol": "tcp",
                        "internal_port": 8080,
                    }
                ],
                "auto_destroy": True,
                "restart": {"policy": "no"},
            },
            "lease_ttl": 86400,  # 24 hours
        }

        print(f"Creating Fly Machine with image: {IDE_IMAGE}")
        response = await client.post(
            f"{FLY_API_BASE}/apps/{FLY_APP_NAME}/machines",
            headers=_headers(),
            json=payload,
        )

        print(f"Fly API response: {response.status_code} {response.text[:500]}")

        if response.status_code not in (200, 201):
            raise Exception(f"Fly API error {response.status_code}: {response.text}")

        return response.json()


async def get_machine(machine_id: str) -> dict:
    """Get the current state of a Fly Machine."""
    async with httpx.AsyncClient(timeout=10) as client:
        response = await client.get(
            f"{FLY_API_BASE}/apps/{FLY_APP_NAME}/machines/{machine_id}",
            headers=_headers(),
        )
        if response.status_code != 200:
            raise Exception(f"Fly API error {response.status_code}: {response.text}")
        return response.json()


async def stop_machine(machine_id: str) -> bool:
    """Stop and destroy a Fly Machine."""
    async with httpx.AsyncClient(timeout=15) as client:
        await client.post(
            f"{FLY_API_BASE}/apps/{FLY_APP_NAME}/machines/{machine_id}/stop",
            headers=_headers(),
        )
        response = await client.delete(
            f"{FLY_API_BASE}/apps/{FLY_APP_NAME}/machines/{machine_id}",
            headers=_headers(),
        )
        return response.status_code in (200, 204)


async def get_machine_url(machine: dict) -> Optional[str]:
    """
    Build the HTTPS URL for a machine.
    Fly assigns a subdomain to each machine: {machine-id}.{app}.fly.dev
    """
    machine_id = machine.get("id", "")
    if not machine_id:
        return None
    return f"https://{machine_id}.vm.{FLY_APP_NAME}.internal:8080"


async def wait_for_machine_ready(machine_id: str, timeout: int = 30) -> bool:
    """Poll until the machine is in 'started' state."""
    import asyncio
    for _ in range(timeout):
        try:
            machine = await get_machine(machine_id)
            state = machine.get("state", "")
            if state == "started":
                return True
            if state in ("destroyed", "failed"):
                return False
        except Exception:
            pass
        await asyncio.sleep(1)
    return False
