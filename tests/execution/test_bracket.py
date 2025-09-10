from algo5.engine.execution.bracket import build_bracket
from algo5.engine.execution.models import OrderType, Side


def test_bracket_constructs_exits_as_oco():
    orders = build_bracket(
        Side.BUY,
        qty=1,
        entry=100.0,
        take_profit=105.0,
        stop_loss=95.0,
        symbol="AAPL",
    )
    assert len(orders) == 3
    entry, tp, sl = orders
    assert getattr(entry, "oco_id", None) in (None, "")
    assert getattr(tp, "oco_id", None) and getattr(sl, "oco_id", None)
    assert tp.oco_id == sl.oco_id
    assert tp.type == OrderType.LIMIT
    assert sl.type in (OrderType.STOP, "TRAILING_STOP")  # trailing seçilmemiş


def test_bracket_trailing_sets_type_and_fields():
    orders = build_bracket(
        Side.SELL,
        qty=2,
        entry=100.0,
        take_profit=95.0,
        stop_loss=105.0,
        trail_amount=1.5,
        symbol="AAPL",
    )
    _, _, sl = orders
    assert str(sl.type).upper() == "TRAILING_STOP"
    assert abs(float(getattr(sl, "trail_amount", 0.0)) - 1.5) < 1e-12
