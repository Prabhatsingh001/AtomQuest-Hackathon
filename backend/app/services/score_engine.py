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
    """
    Compute the achievement score for a goal based on its UoM type.
    
    Returns a float between 0.0 and 1.0.
    """
    if uom_type == "min":
        # Higher is better — actual / target, capped at 1.0
        if not target or target == 0:
            return 0.0
        if actual is None:
            return 0.0
        return min(float(actual) / float(target), 1.0)

    elif uom_type == "max":
        # Lower is better — target / actual, capped at 1.0
        if actual is None or actual == 0:
            return 1.0
        if not target:
            return 0.0
        return min(float(target) / float(actual), 1.0)

    elif uom_type == "zero":
        # Target is implicitly 0 — score 1.0 if actual is 0
        if actual is None:
            return 0.0
        return 1.0 if float(actual) == 0 else 0.0

    elif uom_type == "timeline":
        # Date-based — score 1.0 if completed on or before target date
        if completion_date and target_date:
            return 1.0 if completion_date <= target_date else 0.5
        return 0.0

    return 0.0
