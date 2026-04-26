import hashlib
import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Request

from config import settings
from linear_app.handlers import handle_webhook

logger = logging.getLogger(__name__)

linear_router = APIRouter(prefix="/linear", tags=["linear"])


def _verify_signature(body: bytes, signature: str | None) -> None:
    if not settings.linear_webhook_secret:
        logger.warning("LINEAR_WEBHOOK_SECRET not set; skipping HMAC verification")
        return

    if not signature:
        raise HTTPException(status_code=401, detail="Missing Linear-Signature header")

    expected = hmac.new(
        settings.linear_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


@linear_router.post("/webhook")
async def linear_webhook(
    request: Request,
    linear_signature: str | None = Header(default=None),
):
    body = await request.body()
    _verify_signature(body, linear_signature)

    payload: dict = await request.json()
    await handle_webhook(payload)
    return {"ok": True}
