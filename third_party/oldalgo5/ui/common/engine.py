# ui/engine.py
# Backward-compat shim for old imports: `from ui.engine import ...`
from src.core.backtest.engine import BacktestEngine, FeesConfig
from src.core.risk.engine import RiskEngine
from src.core.risk.config import RiskConfig
from src.core.data import normalize_ohlcv

__all__ = [
    "BacktestEngine",
    "FeesConfig",
    "RiskEngine",
    "RiskConfig",
    "normalize_ohlcv",
]
