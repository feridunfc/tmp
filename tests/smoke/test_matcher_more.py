from algo5.engine.execution.matcher import match_order_on_bar
from algo5.engine.execution.models import TIF, Order, OrderType, Side


def test_stop_sell_gap_fills_at_open():
    """Gap-below: SELL STOP tetiklenir ve open'dan fill olur."""
    od = Order(side=Side.SELL, qty=1, type=OrderType.STOP, stop_price=95.0)
    f = match_order_on_bar(od, o=90.0, h=92.0, low=88.0, c=91.0)
    assert f is not None
    assert f.price == 90.0  # min(o, S) = 90
    assert f.qty == -1  # SELL yönlü


def test_stop_limit_triggered_but_not_crossed_no_fill():
    """STOP tetiklenir ama limit aralığına girmezse aynı barda fill yok."""
    od = Order(
        side=Side.BUY,
        qty=1,
        type=OrderType.STOP_LIMIT,
        stop_price=100.0,  # h >= S → trigger
        limit_price=99.2,  # [low, h] = [99.3, 101] → limit aralık dışında
        tif=TIF.GTC,
    )
    f = match_order_on_bar(od, o=100.0, h=101.0, low=99.3, c=100.0)
    assert f is None
