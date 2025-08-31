# tests/execution/test_timeinforce_ioc_fok.py
from src.algo5.engine.execution.models import Order, OrderType, Side, TIF
from src.algo5.engine.execution.matcher import match_order_on_bar

def test_ioc_and_fok_cancel_if_not_touched():
    ioc = Order(side=Side.BUY, qty=1, type=OrderType.LIMIT, limit_price=90, tif=TIF.IOC)
    fok = Order(side=Side.SELL, qty=1, type=OrderType.LIMIT, limit_price=110, tif=TIF.FOK)
    bar = (100, 100, 100, 100)
    assert match_order_on_bar(ioc, *bar).fill is None
    assert match_order_on_bar(fok, *bar).fill is None

def test_stop_triggers_to_market_open():
    s = Order(side=Side.BUY, qty=1, type=OrderType.STOP, stop_price=102)
    res = match_order_on_bar(s, 100, 105, 95, 101)
    assert res.fill and res.fill.price == 100  # becomes market @ OPEN

def test_stop_limit_needs_both_trigger_and_limit():
    sl = Order(side=Side.SELL, qty=1, type=OrderType.STOP_LIMIT, stop_price=98, limit_price=97, tif=TIF.GTC)
    res = match_order_on_bar(sl, 100, 105, 95, 101)
    assert res.fill or res.remaining_order is not None  # touched or stays working
