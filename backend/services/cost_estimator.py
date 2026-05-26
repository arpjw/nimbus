from __future__ import annotations

import logging
from typing import Optional

from sqlmodel import Session, select, func

from config import settings
from database import engine
from models.token_usage import TokenUsage
from services.llm_client import _PRICE_TABLE, _DEFAULT_PRICE

_log = logging.getLogger(__name__)

_FALLBACK_INPUT_TOKENS_PER_CHANGE = 2_000
_FALLBACK_OUTPUT_TOKENS_PER_CHANGE = 800


def estimate_task_cost(
    n_changes: int,
    planner_cost_incurred: float = 0.0,
    repo_id: Optional[str] = None,
) -> float:
    avg_input, avg_output = _avg_tokens_per_change(repo_id)

    impl_prices = _PRICE_TABLE.get(settings.implementer_model, _DEFAULT_PRICE)
    reviewer_prices = _PRICE_TABLE.get(settings.reviewer_model, _DEFAULT_PRICE)

    impl_cost = (
        avg_input * impl_prices["input"] + avg_output * impl_prices["output"]
    ) / 1_000_000 * n_changes

    reviewer_input = 3_000
    reviewer_output = 400
    review_cost = (
        reviewer_input * reviewer_prices["input"] + reviewer_output * reviewer_prices["output"]
    ) / 1_000_000

    return planner_cost_incurred + impl_cost + review_cost


def _avg_tokens_per_change(repo_id: Optional[str]) -> tuple[float, float]:
    with Session(engine) as session:
        query = select(
            func.avg(TokenUsage.input_tokens),
            func.avg(TokenUsage.output_tokens),
        ).where(TokenUsage.role == "implementer")

        avg_in, avg_out = session.exec(query).one()
        if avg_in and avg_out:
            return float(avg_in), float(avg_out)
    return _FALLBACK_INPUT_TOKENS_PER_CHANGE, _FALLBACK_OUTPUT_TOKENS_PER_CHANGE
