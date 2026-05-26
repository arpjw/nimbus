from __future__ import annotations

from datetime import datetime, timezone
from unittest.mock import MagicMock, patch

import pytest

from services.auth import ApiKey, check_rate_limit


def _make_free_key(task_count: int = 0) -> ApiKey:
    return ApiKey(
        id="test-key",
        key="hashed",
        name="test",
        tier="free",
        task_count_month=task_count,
        created_at=datetime.now(timezone.utc),
    )


def _make_pro_key() -> ApiKey:
    return ApiKey(
        id="pro-key",
        key="hashed",
        name="pro",
        tier="pro",
        task_count_month=9999,
        created_at=datetime.now(timezone.utc),
    )


def _mock_session(count: int) -> MagicMock:
    session = MagicMock()
    session.exec.return_value.one.return_value = count
    return session


@pytest.mark.asyncio
async def test_rate_limit_not_triggered_below_limit():
    key = _make_free_key()
    session = _mock_session(count=5)
    with patch("config.settings") as mock_settings:
        mock_settings.free_tier_monthly_limit = 10
        await check_rate_limit(key, session)


@pytest.mark.asyncio
async def test_rate_limit_triggered_at_limit():
    from fastapi import HTTPException
    key = _make_free_key()
    session = _mock_session(count=10)
    with patch("config.settings") as mock_settings:
        mock_settings.free_tier_monthly_limit = 10
        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit(key, session)
    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_rate_limit_triggered_above_limit():
    from fastapi import HTTPException
    key = _make_free_key()
    session = _mock_session(count=15)
    with patch("config.settings") as mock_settings:
        mock_settings.free_tier_monthly_limit = 10
        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit(key, session)
    assert exc_info.value.status_code == 429


@pytest.mark.asyncio
async def test_pro_tier_not_rate_limited():
    key = _make_pro_key()
    session = _mock_session(count=9999)
    with patch("config.settings") as mock_settings:
        mock_settings.free_tier_monthly_limit = 10
        await check_rate_limit(key, session)


@pytest.mark.asyncio
async def test_rate_limit_boundary_one_below():
    key = _make_free_key()
    session = _mock_session(count=9)
    with patch("config.settings") as mock_settings:
        mock_settings.free_tier_monthly_limit = 10
        await check_rate_limit(key, session)


@pytest.mark.asyncio
async def test_rate_limit_error_message_contains_limit():
    from fastapi import HTTPException
    key = _make_free_key()
    session = _mock_session(count=10)
    with patch("config.settings") as mock_settings:
        mock_settings.free_tier_monthly_limit = 10
        with pytest.raises(HTTPException) as exc_info:
            await check_rate_limit(key, session)
    assert "10" in str(exc_info.value.detail)
