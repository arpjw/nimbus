import hashlib
import hmac
import logging
import time

import httpx
from fastapi import APIRouter, Header, HTTPException, Request
from fastapi.responses import RedirectResponse

from config import settings
from slack_app.handlers import handle_events, handle_slash_command

logger = logging.getLogger(__name__)

router = APIRouter(prefix="/slack", tags=["slack"])


def _verify_slack_signature(body: bytes, timestamp: str | None, signature: str | None) -> None:
    if not settings.slack_signing_secret:
        logger.warning("SLACK_SIGNING_SECRET not set; skipping signature verification")
        return

    if not timestamp or not signature:
        raise HTTPException(status_code=401, detail="Missing Slack signature headers")

    try:
        age = abs(time.time() - int(timestamp))
    except ValueError:
        raise HTTPException(status_code=401, detail="Invalid timestamp")

    if age > 300:
        raise HTTPException(status_code=401, detail="Request timestamp too old")

    sig_basestring = f"v0:{timestamp}:{body.decode()}"
    expected = "v0=" + hmac.new(
        settings.slack_signing_secret.encode(),
        sig_basestring.encode(),
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid Slack signature")


@router.post("/command")
async def slack_command(
    request: Request,
    x_slack_signature: str | None = Header(default=None),
    x_slack_request_timestamp: str | None = Header(default=None),
):
    body = await request.body()
    _verify_slack_signature(body, x_slack_request_timestamp, x_slack_signature)

    form = await request.form()
    payload = dict(form)

    return await handle_slash_command(payload)


@router.post("/events")
async def slack_events(
    request: Request,
    x_slack_signature: str | None = Header(default=None),
    x_slack_request_timestamp: str | None = Header(default=None),
):
    body = await request.body()
    _verify_slack_signature(body, x_slack_request_timestamp, x_slack_signature)

    payload = await request.json()

    if payload.get("type") == "url_verification":
        return {"challenge": payload.get("challenge")}

    await handle_events(payload)
    return {"ok": True}


@router.post("/install")
async def slack_install():
    if not settings.slack_client_id:
        raise HTTPException(status_code=500, detail="SLACK_CLIENT_ID not configured")

    scopes = "chat:write,commands,channels:read"
    redirect_uri = f"{settings.app_base_url}/slack/callback"
    url = (
        f"https://slack.com/oauth/v2/authorize"
        f"?client_id={settings.slack_client_id}"
        f"&scope={scopes}"
        f"&redirect_uri={redirect_uri}"
    )
    return RedirectResponse(url=url)


@router.get("/callback")
async def slack_callback(code: str | None = None, error: str | None = None):
    if error:
        raise HTTPException(status_code=400, detail=f"OAuth error: {error}")

    if not code:
        raise HTTPException(status_code=400, detail="Missing code parameter")

    redirect_uri = f"{settings.app_base_url}/slack/callback"
    async with httpx.AsyncClient() as client:
        resp = await client.post(
            "https://slack.com/api/oauth.v2.access",
            data={
                "client_id": settings.slack_client_id,
                "client_secret": settings.slack_client_secret,
                "code": code,
                "redirect_uri": redirect_uri,
            },
        )

    data = resp.json()
    if not data.get("ok"):
        raise HTTPException(status_code=400, detail=f"OAuth failed: {data.get('error')}")

    return {
        "ok": True,
        "team": data.get("team", {}).get("name"),
        "message": "Nimbus installed successfully",
    }
