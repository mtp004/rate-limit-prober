import pytest

from prober import predicted_success_p, solve_decrease_frac


@pytest.mark.parametrize("i", [0.05, 0.2, 0.6, 1.0])
@pytest.mark.parametrize("p", [0.9, 0.99, 0.999])
def test_solve_is_inverse_of_predict(i, p):
    d = solve_decrease_frac(i, p)
    assert predicted_success_p(d, i) == pytest.approx(p)


def test_symmetric_steps_give_half():
    assert predicted_success_p(0.5, 1.0) == pytest.approx(0.5)
