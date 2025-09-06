"""Updated adapter to call run_vector_backtest and keep backward compatibility.
Use run_backtest_v3 to call new engine with defaults merged.
"""

from src.config.defaults_loader import merge_backtest_defaults

try:
    from src.core.backtest.engine_v2 import run_vector_backtest
except Exception as e:
    raise ImportError(f"Could not import run_vector_backtest: {e}") from e


def run_backtest_v3(prices, strategy_fn, cfg=None, capital=100000.0, project_root=None, freq="D"):
    cfg = cfg or {}
    cfg = merge_backtest_defaults(cfg, project_root=project_root)
    return run_vector_backtest(prices, strategy_fn, cfg=cfg, capital=capital, freq=freq)
