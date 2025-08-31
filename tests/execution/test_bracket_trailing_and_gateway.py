# tests/execution/test_bracket_trailing_and_gateway.py
from src.algo5.engine.execution.models import Order, OrderType, Side, BracketOrder, TrailingStopOrder, TIF
from src.algo5.engine.execution.gateways.paper import PaperGateway

def test_bracket_children_staged_after_parent_fill():
    gw = PaperGateway()
    # first bar arrives
    gw.on_bar(100, 103, 99, 101)

    parent = Order(side=Side.BUY, qty=1, type=OrderType.MARKET)
    tp = Order(side=Side.SELL, qty=1, type=OrderType.LIMIT, limit_price=105)
    sl = Order(side=Side.SELL, qty=1, type=OrderType.STOP,  stop_price=95)
    pid = gw.submit_bracket(BracketOrder(parent=parent, tp_order=tp, sl_order=sl))

    # parent fill immediately @100, children should be in book
    assert any(k.startswith(pid) for k in gw.orders.keys())

def test_trailing_stop_exits_on_pullback():
    gw = PaperGateway()
    gw.on_bar(100, 101, 99, 100)

    tr = TrailingStopOrder(side=Side.BUY, qty=1, type=OrderType.STOP, trail_amount=2.0)
    oid = gw.submit_trailing(tr)
    assert oid in gw.trailing_orders

    # rally: peak=108; no exit
    gw.on_bar(101, 108, 100, 107)
    assert gw.trailing_orders[oid].peak_price == 108

    # pullback: low touches 106 (peak 108 - 2) → exit market @ bar OPEN (107)
    fills = gw.on_bar(107, 107, 105.9, 106)
    assert any(f.price == 107 for f in fills) or any(f.price == 107 for f in gw.fills)

def test_gateway_determinism():
    bars = [(100,103,99,102),(101,104,100,103),(102,105,101,104)]
    def run():
        gw = PaperGateway()
        gw.submit(Order(side=Side.BUY, qty=1, type=OrderType.MARKET))  # no bar yet → book if GTC
        out = []
        for b in bars:
            out.extend(gw.on_bar(*b))
        return [(f.price, f.qty) for f in out]  # only filled
    a, b = run(), run()
    assert a == b
