from __future__ import annotations

import hashlib
import hmac
from unittest.mock import patch

import pytest

from github_app.webhooks import _verify_signature
from fastapi import HTTPException


def _make_signature(secret: str, body: bytes) -> str:
    return "sha256=" + hmac.new(secret.encode(), body, hashlib.sha256).hexdigest()


def test_valid_signature_passes():
    body = b'{"action": "opened"}'
    sig = _make_signature("test-secret", body)
    with patch("github_app.webhooks.settings") as mock_settings:
        mock_settings.github_webhook_secret = "test-secret"
        _verify_signature(body, sig)


def test_invalid_signature_raises_401():
    body = b'{"action": "opened"}'
    with patch("github_app.webhooks.settings") as mock_settings:
        mock_settings.github_webhook_secret = "test-secret"
        with pytest.raises(HTTPException) as exc_info:
            _verify_signature(body, "sha256=deadbeef")
    assert exc_info.value.status_code == 401


def test_missing_signature_raises_401():
    body = b'{"action": "opened"}'
    with patch("github_app.webhooks.settings") as mock_settings:
        mock_settings.github_webhook_secret = "test-secret"
        with pytest.raises(HTTPException) as exc_info:
            _verify_signature(body, None)
    assert exc_info.value.status_code == 401


def test_malformed_signature_raises_401():
    body = b'{"action": "opened"}'
    with patch("github_app.webhooks.settings") as mock_settings:
        mock_settings.github_webhook_secret = "test-secret"
        with pytest.raises(HTTPException):
            _verify_signature(body, "notsha256=something")


def test_no_secret_configured_skips_verification():
    body = b'{"action": "opened"}'
    with patch("github_app.webhooks.settings") as mock_settings:
        mock_settings.github_webhook_secret = ""
        _verify_signature(body, None)


def test_tampered_body_rejected():
    original = b'{"action": "opened"}'
    tampered = b'{"action": "closed"}'
    sig = _make_signature("test-secret", original)
    with patch("github_app.webhooks.settings") as mock_settings:
        mock_settings.github_webhook_secret = "test-secret"
        with pytest.raises(HTTPException) as exc_info:
            _verify_signature(tampered, sig)
    assert exc_info.value.status_code == 401
