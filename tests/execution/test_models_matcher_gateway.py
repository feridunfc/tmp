from algo5.engine.execution.models import OrderType, Side, Order
from algo5.engine.execution.matcher import match_order_on_bar
from algo5.engine.execution.gateways.paper import PaperGateway

def test_limit_buy_match():
    order = Order(side=Side.BUY, qty=1, type=OrderType.LIMIT, limit_price=10.0)
    fill = match_order_on_bar(order, o=9, h=11, l=8, c=10)
    assert fill is not None
    assert abs(fill.price - 10.0) < 1e-9

def test_paper_gateway_uses_matcher():
    gw = PaperGateway()
    gw.on_bar(9, 11, 8, 10)
    order = Order(side=Side.BUY, qty=2, type=OrderType.LIMIT, limit_price=10.0)
    fill = gw.submit(order)
    assert fill is not None
    assert len(gw.fills) == 1
