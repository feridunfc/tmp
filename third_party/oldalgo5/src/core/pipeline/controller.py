from __future__ import annotations
from typing import Dict, Any, Tuple
import pandas as pd

# soft imports to avoid hard coupling in tests
try:
    from core.backtest.engine import BacktestEngine
    from core.backtest.engine import FeesConfig
except Exception:  # pragma: no cover
    BacktestEngine = object  # type: ignore
    FeesConfig = object  # type: ignore

try:
    from strategies.registry import get_strategy
except Exception:  # pragma: no cover
    def get_strategy(name: str, **kwargs):  # type: ignore
        raise RuntimeError("get_strategy unavailable")

try:
    from app_signals.overlay import apply_overlays
except Exception:  # pragma: no cover
    def apply_overlays(sig, df, **kwargs):  # type: ignore
        return sig, {}

class PipelineController:
    """Minimal pipeline controller for single backtest with overlays."""

    def run_single(
        self,
        df: pd.DataFrame,
        strategy_name: str,
        strategy_params: Dict[str, Any],
        fees_config: Any,
        risk_engine: Any = None,
        overlay_kwargs: Dict[str, Any] | None = None,
    ) -> Dict[str, Any]:
        strat = get_strategy(strategy_name, **strategy_params)
        prepared = strat.prepare(df)
        raw_sig = strat.generate_signals(prepared)
        net_sig, meta = apply_overlays(raw_sig, prepared, **(overlay_kwargs or {}))

        eng = BacktestEngine(fees_config=fees_config, risk_engine=risk_engine)
        result = eng.run_backtest(prepared, net_sig)
        result.setdefault("meta", {}).update({"overlay": meta})
        return result
