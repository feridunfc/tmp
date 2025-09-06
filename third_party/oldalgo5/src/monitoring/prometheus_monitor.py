
from __future__ import annotations
from typing import Optional

try:
    from prometheus_client import Counter, Gauge, Histogram  # type: ignore
    _PROM = True
except Exception:
    _PROM = False

class PrometheusMonitor:
    def __init__(self):
        if _PROM:
            self.trades_counter = Counter('algo_trades_total','Total trades',['symbol','side'])
            self.signals_counter = Counter('algo_signals_total','Total signals',['symbol','direction'])
            self.portfolio_value = Gauge('algo_portfolio_value','Current portfolio value')
            self.drawdown_gauge = Gauge('algo_drawdown','Current drawdown percentage')
            self.latency_histogram = Histogram('algo_latency_seconds','Trade latency')
        else:
            self.trades_counter = self.signals_counter = self.portfolio_value = self.drawdown_gauge = self.latency_histogram = None

    def on_fill(self, symbol: str, side: str, latency: float = None):
        if not _PROM: return
        self.trades_counter.labels(symbol=symbol, side=side).inc()
        if latency is not None:
            self.latency_histogram.observe(float(latency))

    def on_signal(self, symbol: str, direction: str):
        if not _PROM: return
        self.signals_counter.labels(symbol=symbol, direction=direction).inc()

    def update_portfolio(self, value: float, drawdown: float):
        if not _PROM: return
        self.portfolio_value.set(float(value))
        self.drawdown_gauge.set(float(drawdown))
