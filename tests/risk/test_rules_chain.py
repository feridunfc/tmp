from algo5.engine.risk import RiskContext, FixedSizer, PercentNotionalSizer, MaxPositionQty, MaxNotional, RiskChain
from algo5.engine.execution.models import Side, OrderType

def test_chain_caps_by_maxpos():
    ctx = RiskContext(capital=100_000, position_qty=0.0, last_price=100.0)
    sizer = PercentNotionalSizer(percent=0.10)  # 10% -> 100 adet @100
    chain = RiskChain(rules=[MaxPositionQty(max_qty=50)], sizer=sizer)
    ord = chain.propose(Side.BUY, ctx, order_type=OrderType.MARKET)
    assert ord is not None
    assert abs(ord.qty - 50.0) < 1e-9

def test_chain_caps_by_notional():
    ctx = RiskContext(capital=100_000, position_qty=0.0, last_price=200.0)
    sizer = FixedSizer(qty=1_000.0)             # çok büyük istenir
    chain = RiskChain(rules=[MaxNotional(max_notional=10_000)], sizer=sizer)
    ord = chain.propose(Side.BUY, ctx, order_type=OrderType.MARKET)
    assert ord is not None
    # max qty = 10_000 / 200 = 50
    assert abs(ord.qty - 50.0) < 1e-9
