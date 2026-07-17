from catalyst_finance.elasticity import (
    classify,
    discrete_mr,
    midpoint_elasticity,
    point_elasticity_linear,
)


def test_midpoint_elasticity() -> None:
    result = midpoint_elasticity(10, 12, 100, 80)
    assert round(result, 6) == round((-20 / 90) / (2 / 11), 6)


def test_point_elasticity_linear() -> None:
    assert point_elasticity_linear(100, 2, 25) == -1.0
    assert classify(1.0) == "unit elastic"


def test_discrete_marginal_revenue() -> None:
    prices, values = discrete_mr([1, 2, 3], [10, 18, 24])
    assert prices == [2, 3]
    assert values == [8, 6]
