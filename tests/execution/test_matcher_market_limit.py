# tests/execution/test_matcher_market_limit.py
from src.algo5.engine.execution.models import Order, OrderType, Side, TIF
from src.algo5.engine.execution.matcher import match_order_on_bar, match_on_bar

def test_market_fills_at_open():
    o = Order(side=Side.BUY, qty=1, type=OrderType.MARKET)
    res = match_order_on_bar(o, 100, 102, 98, 101)
    assert res.fill and res.fill.price == 100 and res.fill.qty == 1

def test_limit_buy_sell_touch_and_minmax_rule():
    buy = Order(side=Side.BUY, qty=1, type=OrderType.LIMIT, limit_price=99)
    sell = Order(side=Side.SELL, qty=1, type=OrderType.LIMIT, limit_price=108)
    bar = {"Open":100, "High":110, "Low":90, "Close":105}
    rb = match_on_bar(buy, bar); rs = match_on_bar(sell, bar)
    assert rb.fill and rb.fill.price == 99
    assert rs.fill and rs.fill.price == 108

def test_limit_ioc_cancels_when_not_touched():
    ioc = Order(side=Side.BUY, qty=1, type=OrderType.LIMIT, limit_price=95, tif=TIF.IOC)
    res = match_order_on_bar(ioc, 100, 101, 99, 100)
    assert res.fill is None and res.remaining_order is None
