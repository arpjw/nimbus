import hashlib
import hmac
import logging

from fastapi import APIRouter, Header, HTTPException, Request

from config import settings
from github_app.handlers import (
    handle_issue_comment,
    handle_issues,
    handle_pull_request,
    handle_pull_request_review,
    handle_issue_comment_reaction,
)

logger = logging.getLogger(__name__)

router = APIRouter(tags=["github"])


def _verify_signature(body: bytes, signature: str | None) -> None:
    if not settings.github_webhook_secret:
        logger.warning("GITHUB_WEBHOOK_SECRET not set; skipping HMAC verification")
        return

    if not signature or not signature.startswith("sha256="):
        raise HTTPException(status_code=401, detail="Missing or malformed X-Hub-Signature-256")

    expected = "sha256=" + hmac.new(
        settings.github_webhook_secret.encode(),
        body,
        hashlib.sha256,
    ).hexdigest()

    if not hmac.compare_digest(expected, signature):
        raise HTTPException(status_code=401, detail="Invalid webhook signature")


@router.post("/github/webhook")
async def github_webhook(
    request: Request,
    x_hub_signature_256: str | None = Header(default=None),
    x_github_event: str | None = Header(default=None),
):
    body = await request.body()
    _verify_signature(body, x_hub_signature_256)

    payload: dict = await request.json()

    if x_github_event == "issue_comment":
        await handle_issue_comment(payload)
    elif x_github_event == "issues":
        await handle_issues(payload)
    elif x_github_event == "pull_request":
        await handle_pull_request(payload)
    elif x_github_event == "pull_request_review":
        await handle_pull_request_review(payload)
    elif x_github_event == "reaction":
        await handle_issue_comment_reaction(payload)
    else:
        logger.debug("Unhandled GitHub event: %s", x_github_event)

    return {"ok": True}
