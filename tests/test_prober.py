import pytest

from prober import (LIMITERS, SMOOTHERS, HALT_RULES, run_prober,
                    solve_decrease_frac)

P = 0.99
I = 0.60
D = solve_decrease_frac(I, P)


@pytest.mark.parametrize("lim_name", ["fixed", "rolling"])
@pytest.mark.parametrize("limit,window", [(5, 10.0), (20, 5.0), (50, 3600.0)])
def test_cycle_rule_lands_near_true_gap(lim_name, limit, window):
    true_gap = window / limit
    res = run_prober(
        LIMITERS[lim_name](limit, window),
        initial_gap=0.5 * true_gap,
        decrease_frac=D, increase_frac=I,
        smoother=SMOOTHERS["sma"](100),
        halt_rule=HALT_RULES["cycle"](P),
    )
    assert res.converged
    assert abs(res.estimate / true_gap - 1) < 0.02


def test_success_rate_matches_target():
    limit, window = 10, 5.0
    res = run_prober(
        LIMITERS["fixed"](limit, window),
        initial_gap=0.5 * window / limit,
        decrease_frac=D, increase_frac=I,
        smoother=SMOOTHERS["sma"](100),
        halt_rule=HALT_RULES["none"](),
        n_iters=20000,
    )
    tail = [ok for _, _, ok in res.trace[-5000:]]
    assert sum(tail) / len(tail) == pytest.approx(P, abs=0.005)


def test_latency_run_is_reproducible():
    kwargs = dict(initial_gap=0.1, decrease_frac=D, increase_frac=I,
                  rtt=0.3, jitter=0.1, n_iters=2000, seed=7)
    a = run_prober(LIMITERS["rolling"](20, 5.0), smoother=SMOOTHERS["sma"](100),
                   halt_rule=HALT_RULES["none"](), **kwargs)
    b = run_prober(LIMITERS["rolling"](20, 5.0), smoother=SMOOTHERS["sma"](100),
                   halt_rule=HALT_RULES["none"](), **kwargs)
    assert [g for _, g, _ in a.trace] == [g for _, g, _ in b.trace]
