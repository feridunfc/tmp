from algo5.monitoring.prometheus import REGISTRY
from algo5.monitoring.health import HealthChecker
def test_metrics_and_health():
    c = REGISTRY.counter("orders_total","Number of orders"); c.inc(); c.inc(2); assert c.value == 3
    g = REGISTRY.gauge("latency_ms","Latency gauge"); g.set(42); assert g.value == 42.0
    h = HealthChecker(); h.add_check("ok", lambda: True); h.add_check("fail", lambda: False)
    out = h.run(); assert out["ok"] is True and out["fail"] is False
