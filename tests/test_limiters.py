import pytest

from prober import FixedWindowLimiter, RollingWindowLimiter


@pytest.mark.parametrize("cls", [FixedWindowLimiter, RollingWindowLimiter])
@pytest.mark.parametrize("limit,window", [(5, 10.0), (20, 5.0), (3, 0.3), (50, 3600.0)])
def test_constant_gap_at_true_rate_never_rejected(cls, limit, window):
    lim = cls(limit, window)
    gap = window / limit * (1 + 1e-9)  # float rounding, e.g. 0.3 / 3
    assert all(lim.request(k * gap) for k in range(20 * limit))


@pytest.mark.parametrize("cls", [FixedWindowLimiter, RollingWindowLimiter])
def test_slightly_too_fast_gets_rejected(cls):
    limit, window = 10, 5.0
    lim = cls(limit, window)
    gap = 0.95 * window / limit
    results = [lim.request(k * gap) for k in range(2000)]
    assert not all(results)


@pytest.mark.parametrize("cls", [FixedWindowLimiter, RollingWindowLimiter])
def test_burst_accepts_exactly_limit(cls):
    lim = cls(7, 1.0)
    results = [lim.request(0.0) for _ in range(20)]
    assert sum(results) == 7
    assert results[:7] == [True] * 7
