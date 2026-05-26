from __future__ import annotations

import logging
import time
from typing import Any, Optional
from datetime import datetime, timezone, timedelta

import anthropic
from tenacity import (
    retry,
    retry_if_exception,
    stop_after_attempt,
    wait_exponential,
    before_sleep_log,
)

from config import settings

_log = logging.getLogger(__name__)

_CIRCUIT_WINDOW = 60.0
_CIRCUIT_THRESHOLD = 10
_CIRCUIT_COOLDOWN = 60.0

_circuit_failures: list[float] = []
_circuit_open_until: float = 0.0


def _is_retryable(exc: BaseException) -> bool:
    if isinstance(exc, anthropic.APIStatusError):
        return exc.status_code in (408, 429, 500, 502, 503, 504, 529)
    return isinstance(exc, anthropic.APIConnectionError)


def _check_circuit() -> None:
    global _circuit_open_until
    now = time.monotonic()
    if now < _circuit_open_until:
        raise anthropic.APIConnectionError(request=None, message="Circuit breaker open -- too many consecutive failures")


def _record_failure() -> None:
    global _circuit_open_until
    now = time.monotonic()
    _circuit_failures.append(now)
    cutoff = now - _CIRCUIT_WINDOW
    while _circuit_failures and _circuit_failures[0] < cutoff:
        _circuit_failures.pop(0)
    if len(_circuit_failures) >= _CIRCUIT_THRESHOLD:
        _circuit_open_until = now + _CIRCUIT_COOLDOWN
        _circuit_failures.clear()


def _record_success() -> None:
    global _circuit_open_until
    _circuit_failures.clear()
    _circuit_open_until = 0.0

_PRICE_TABLE: dict[str, dict[str, float]] = {
    "claude-opus-4-7": {"input": 15.0, "output": 75.0, "cache_read": 1.50, "cache_write": 18.75},
    "claude-opus-4-6": {"input": 15.0, "output": 75.0, "cache_read": 1.50, "cache_write": 18.75},
    "claude-sonnet-4-6": {"input": 3.0, "output": 15.0, "cache_read": 0.30, "cache_write": 3.75},
    "claude-haiku-4-5": {"input": 0.80, "output": 4.0, "cache_read": 0.08, "cache_write": 1.0},
    "claude-haiku-4-5-20251001": {"input": 0.80, "output": 4.0, "cache_read": 0.08, "cache_write": 1.0},
}
_DEFAULT_PRICE = {"input": 3.0, "output": 15.0, "cache_read": 0.30, "cache_write": 3.75}


def _compute_cost(model: str, usage) -> float:
    prices = _PRICE_TABLE.get(model, _DEFAULT_PRICE)
    input_tokens = getattr(usage, "input_tokens", 0) or 0
    output_tokens = getattr(usage, "output_tokens", 0) or 0
    cache_read = getattr(usage, "cache_read_input_tokens", 0) or 0
    cache_write = getattr(usage, "cache_creation_input_tokens", 0) or 0
    return (
        input_tokens * prices["input"]
        + output_tokens * prices["output"]
        + cache_read * prices["cache_read"]
        + cache_write * prices["cache_write"]
    ) / 1_000_000


def _persist_usage(
    model: str,
    role: str,
    task_id: Optional[str],
    api_key_id: Optional[str],
    usage,
    cost: float,
) -> None:
    try:
        from database import engine
        from sqlmodel import Session
        from models.token_usage import TokenUsage

        row = TokenUsage(
            task_id=task_id,
            api_key_id=api_key_id,
            provider="anthropic",
            model=model,
            role=role,
            input_tokens=getattr(usage, "input_tokens", 0) or 0,
            output_tokens=getattr(usage, "output_tokens", 0) or 0,
            cache_read_tokens=getattr(usage, "cache_read_input_tokens", 0) or 0,
            cache_creation_tokens=getattr(usage, "cache_creation_input_tokens", 0) or 0,
            cost_usd=cost,
        )
        with Session(engine) as session:
            session.add(row)
            session.commit()
    except Exception:
        pass


class _InstrumentedMessages:
    def __init__(self, inner, role: str, task_id: Optional[str], api_key_id: Optional[str]) -> None:
        self._inner = inner
        self._role = role
        self._task_id = task_id
        self._api_key_id = api_key_id

    async def create(self, **kwargs: Any):
        _check_circuit()
        model = kwargs.get("model", "")

        @retry(
            retry=retry_if_exception(_is_retryable),
            wait=wait_exponential(multiplier=1, min=2, max=30),
            stop=stop_after_attempt(5),
            before_sleep=before_sleep_log(_log, logging.WARNING),
            reraise=True,
        )
        async def _call():
            return await self._inner.create(**kwargs)

        try:
            response = await _call()
            _record_success()
        except Exception:
            _record_failure()
            raise

        try:
            cost = _compute_cost(model, response.usage)
            _persist_usage(model, self._role, self._task_id, self._api_key_id, response.usage, cost)
        except Exception:
            pass
        return response


class _InstrumentedClient:
    def __init__(self, inner: anthropic.AsyncAnthropic, role: str, task_id: Optional[str], api_key_id: Optional[str]) -> None:
        self._inner = inner
        self.messages = _InstrumentedMessages(inner.messages, role, task_id, api_key_id)


def _resolve_anthropic_key(api_key_id: Optional[str]) -> tuple[str, bool]:
    """Returns (api_key_str, is_byok). Falls back to server key if no BYOK configured."""
    if not api_key_id:
        return settings.anthropic_api_key, False
    try:
        from database import engine
        from sqlmodel import Session
        from services.auth import ApiKey

        with Session(engine) as session:
            record = session.get(ApiKey, api_key_id)
            if record and record.user_anthropic_key_encrypted:
                decrypted = _decrypt_value(record.user_anthropic_key_encrypted)
                if decrypted:
                    return decrypted, True
    except Exception:
        pass
    return settings.anthropic_api_key, False


def _decrypt_value(value: str) -> str:
    import base64
    import hashlib

    enc_key = settings.encryption_key
    if not enc_key:
        return value
    try:
        from cryptography.fernet import Fernet

        key = base64.urlsafe_b64encode(hashlib.sha256(enc_key.encode()).digest())
        return Fernet(key).decrypt(value.encode()).decode()
    except Exception:
        return value


def instrumented_anthropic_client(
    role: str,
    task_id: Optional[str] = None,
    api_key_id: Optional[str] = None,
) -> _InstrumentedClient:
    resolved_key, is_byok = _resolve_anthropic_key(api_key_id)
    base = anthropic.AsyncAnthropic(api_key=resolved_key)
    client = _InstrumentedClient(base, role, task_id, api_key_id)
    client._is_byok = is_byok
    return client


async def check_spend_cap(api_key_id: str) -> None:
    try:
        from database import engine
        from sqlmodel import Session, select, func
        from models.token_usage import TokenUsage
        from services.auth import ApiKey

        with Session(engine) as session:
            api_key = session.get(ApiKey, api_key_id)
            if not api_key:
                return

            if api_key.user_anthropic_key_encrypted:
                return

            cap = 5.0 if api_key.tier == "free" else 100.0
            since = datetime.now(timezone.utc) - timedelta(days=30)
            spent = session.exec(
                select(func.sum(TokenUsage.cost_usd)).where(
                    TokenUsage.api_key_id == api_key_id,
                    TokenUsage.created_at >= since,
                )
            ).one() or 0.0

            if spent >= cap:
                from fastapi import HTTPException
                raise HTTPException(
                    status_code=429,
                    detail=f"Monthly spend cap of ${cap:.2f} reached (spent ${spent:.4f})",
                )
    except Exception as exc:
        from fastapi import HTTPException
        if isinstance(exc, HTTPException):
            raise
