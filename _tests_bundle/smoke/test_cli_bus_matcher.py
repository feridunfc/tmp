# tests/smoke/test_cli_bus_matcher.py
from __future__ import annotations
import sys

from algo5.core.bus import EventBus
from algo5.engine.execution.models import Order, OrderType, Side, TIF
from algo5.engine.execution.matcher import match_order_on_bar


def test_cli_main_smoke(monkeypatch, capsys):
    """CLI main() akışını çalıştırır; runtime.py satırlarını kaplar."""
    # sys.argv'ı CLI gibi taklit et
    monkeypatch.setattr(
        sys,
        "argv",
        ["algo5-sim", "--bars", "1", "--symbol", "AAPL", "--o", "100"],
    )
    from algo5.app import runtime  # içe aktarmayı test fonksiyonu içinde yap

    runtime.main()
    out = capsys.readouterr().out
    assert "equity=" in out  # çıktıdan küçük bir işaret yeterli


def test_eventbus_handler_exception_logs(caplog):
    """EventBus publish sırasında handler exception yolunu tetikler."""

    class Dummy:  # basit bir event tipi
        pass

    def bad_handler(_e, _bus):
        raise RuntimeError("boom")

    bus = EventBus()
    bus.subscribe(Dummy, bad_handler)

    with caplog.at_level("ERROR"):
        bus.publish(Dummy())

    assert "boom" in caplog.text or "handler" in caplog.text


def test_matcher_limit_ioc_no_cross():
    """Limit IOC bar aralığına girmeyince fill olmaz (None döner)."""
    od = Order(
        side=Side.BUY,
        qty=1.0,
        type=OrderType.LIMIT,
        limit_price=95.0,  # bar [o=100,h=101,low=99,c=100] içinde değil
        tif=TIF.IOC,
    )
    f = match_order_on_bar(od, o=100.0, h=101.0, low=99.0, c=100.0)
    assert f is None
