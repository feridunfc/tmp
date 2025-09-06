from algo5.engine.execution.gateways.paper import PaperGateway
from algo5.engine.execution.matcher import match_order_on_bar
from algo5.engine.execution.models import Order, OrderType, Side


def test_market_fills_at_open():
    od = Order(side=Side.BUY, qty=10, type=OrderType.MARKET)
    f = match_order_on_bar(od, o=100, h=101, low=99, c=100)
    assert f is not None and f.price == 100 and f.qty == 10


def test_limit_buy_crosses_low_high():
    od = Order(side=Side.BUY, qty=1, type=OrderType.LIMIT, limit_price=99.5)
    f = match_order_on_bar(od, o=100, h=101, low=99, c=100)
    assert f is not None and f.price == 99.5


def test_stop_sell_triggers_on_low():
    od = Order(side=Side.SELL, qty=1, type=OrderType.STOP, stop_price=99.5)
    f = match_order_on_bar(od, o=100, h=101, low=99, c=100)
    assert f is not None and f.price == 99.5  # gap yoksa stop fiyatÄ±


def test_paper_gateway_simple_roundtrip():
    gw = PaperGateway(initial_capital=1_000.0, fees_bps=0.0, slippage_bps=0.0)
    # 1) market buy 1@o=100 â†’ pos=1 cash=900
    gw.submit(Order(side=Side.BUY, qty=1, type=OrderType.MARKET))
    gw.on_bar(o=100, h=101, low=99, c=100)
    st = gw.state(100)
    assert st["pos"] == 1 and st["cash"] == 900

    # 2) sell limit 1@101 â†’ fill olur, pos=0, cash=1001, equity=1001
    gw.submit(Order(side=Side.SELL, qty=1, type=OrderType.LIMIT, limit_price=101))
    gw.on_bar(o=100.5, h=101.5, low=100, c=101)
    st = gw.state(101)
    assert st["pos"] == 0 and round(st["equity"], 2) == 1001.0


def test_stop_limit_requires_both_conditions():
    # stop tetikler ama limit ÅŸartÄ± yoksa fill olmaz (aynÄ± bar)
    od = Order(
        side=Side.BUY,
        qty=1,
        type=OrderType.STOP_LIMIT,
        stop_price=100,
        limit_price=99.2,
    )
    f = match_order_on_bar(od, o=100, h=101, low=99.3, c=100)
    assert f is None

    # hem stop tetikler hem limit Ã§aprazlanÄ±rsa fill
    f2 = match_order_on_bar(od, o=100, h=101, low=99.0, c=100)
    assert f2 is not None
