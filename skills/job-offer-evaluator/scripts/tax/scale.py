"""Progressive tax scales: pure functions, no country knowledge and no I/O.

A scale is a list of `[upper_limit, rate]` pairs in ascending order, where the last pair has
`upper_limit = None` (no ceiling). Rates are fractions (0.095 = 9.5%).
"""
from typing import Optional, Sequence, Tuple

Scale = Sequence[Tuple[Optional[float], float]]


def apply_scale(scale: Scale, base: float, shift: float = 0.0) -> float:
    """Apply a progressive scale to `base`: each slice of income is taxed at its own rate.

    Example: with brackets 9.5% up to 12,450 and 12% up to 20,200, a base of 15,000 pays
    12,450 * 9.5% + 2,550 * 12%. `shift` is added to every rate (never going below 0).
    """
    tax, prev = 0.0, 0.0
    for top, rate in scale:
        top = float("inf") if top is None else top   # last bracket has no upper limit
        if base > prev:
            tax += (min(base, top) - prev) * max(rate + shift, 0)
        prev = top
    return tax


def tax_net_of_minimum(scale: Scale, base: float, minimum: float, shift: float = 0.0) -> float:
    """Tax on `base` after the personal minimum, the way Spanish IRPF does it.

    The minimum is not subtracted from income: the scale is applied to the whole base and then the
    tax that the minimum itself would generate is subtracted (never below 0).
    """
    return max(apply_scale(scale, base, shift) - apply_scale(scale, minimum, shift), 0.0)
