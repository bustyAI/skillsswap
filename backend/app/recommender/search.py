"""Vector search and ranking for mentor recommendations."""

import math
from datetime import UTC, datetime
from decimal import Decimal


def _compute_activity_recency(last_active_at: datetime | None) -> float:
    """Compute activity recency score using exponential decay.

    Returns exp(-days_since_last_active / 30).
    If last_active_at is None, returns 0.5 as default.
    """
    if last_active_at is None:
        return 0.5

    now = datetime.now(UTC)
    if last_active_at.tzinfo is None:
        last_active_at = last_active_at.replace(tzinfo=UTC)

    days_since = (now - last_active_at).total_seconds() / 86400
    return math.exp(-days_since / 30)


def _compute_normalized_rating(
    rating_avg: Decimal | None,
    rating_count: int,
) -> float:
    """Compute normalized rating score.

    Returns rating_avg / 5.0.
    If rating_count < 3, returns 0.5 (not enough data for confidence).
    """
    if rating_count < 3 or rating_avg is None:
        return 0.5

    return float(rating_avg) / 5.0


def _compute_moderation_penalty(open_reports_count: int) -> float:
    """Compute moderation penalty based on open reports.

    Returns min(1.0, open_reports_count / 10).
    """
    return min(1.0, open_reports_count / 10)
