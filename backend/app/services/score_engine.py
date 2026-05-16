"""Score engine — pure functions for computing goal scores."""

from decimal import Decimal
from datetime import date
from typing import Optional


def compute_score(
    uom_type: str,
    target: Optional[Decimal],
    actual: Optional[Decimal],
    target_date: Optional[date] = None,
    completion_date: Optional[date] = None,
) -> float:
    """Calculate the normalized achievement score for a goal based on its unit of measurement.

    Args:
        uom_type: Unit of measurement classification ('min', 'max', 'zero', 'timeline').
        target: Target numeric threshold.
        actual: Recorded actual figure achieved.
        target_date: Target deadline date for timeline goals.
        completion_date: Recorded completion date for timeline goals.

    Returns:
        float: Normalized performance score bounded between 0.0 and 1.0.
    """
    if uom_type == "min":
        if not target or target == 0:
            return 0.0
        if actual is None:
            return 0.0
        return min(float(actual) / float(target), 1.0)

    elif uom_type == "max":
        if actual is None or actual == 0:
            return 1.0
        if not target:
            return 0.0
        return min(float(target) / float(actual), 1.0)

    elif uom_type == "zero":
        if actual is None:
            return 0.0
        return 1.0 if float(actual) == 0 else 0.0

    elif uom_type == "timeline":
        if completion_date and target_date:
            return 1.0 if completion_date <= target_date else 0.5
        return 0.0

    return 0.0
