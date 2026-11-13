import math


def predicted_success_p(decrease_frac, increase_frac):
    """Success rate at which the log-gap has zero drift.

    Exact for the unsmoothed update. With SMA/EMA smoothing it is a good
    approximation only when decrease_frac is much smaller than increase_frac.
    """
    d, i = decrease_frac, increase_frac
    return math.log(1 + i) / (math.log(1 + i) - math.log(1 - d))


def solve_decrease_frac(increase_frac, target_p):
    """Inverse of predicted_success_p: pick d for a given i and target success rate."""
    i, p = increase_frac, target_p
    return 1 - (1 + i) ** (-(1 - p) / p)
