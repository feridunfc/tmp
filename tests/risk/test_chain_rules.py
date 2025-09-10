import pandas as pd
from algo5.engine.risk.rules import MaxPositionRule, CoolDownRule, FloorCapRule, DrawdownGuardRule


def test_maxposition_clamps():
    w = pd.Series({"A": 1.2, "B": 0.05})
    out = MaxPositionRule(max_w=0.1).apply(pd.Series(dtype=float), w)
    assert out["A"] == 0.1 and out["B"] == 0.05


def test_cooldown_scales_down():
    w = pd.Series({"A": 0.4})
    out = CoolDownRule(n_bars=3, reduction=0.25).apply(
        pd.Series(dtype=float), w, {"recent_loss": True}
    )
    assert abs(out["A"] - 0.1) < 1e-9


def test_floorcap_bounds():
    w = pd.Series({"A": -0.2, "B": 0.5, "C": 1.5})
    out = FloorCapRule(floor=0.0, cap=1.0).apply(pd.Series(dtype=float), w)
    assert out["A"] == 0.0 and out["B"] == 0.5 and out["C"] == 1.0


def test_drawdown_guard_optional():
    eq = pd.Series([100, 90, 85])
    w = pd.Series({"A": 0.5})
    out = DrawdownGuardRule(dd_window=10, max_dd=0.1).apply(
        pd.Series(dtype=float), w, {"equity_curve": eq}
    )
    assert out["A"] < 0.5
