
# ui/tabs/walk_tab.py (import kısmı için örnek)
try:
    from src.core.backtest.walkforward import run_walkforward  # algo2 sürümü
except ImportError:
    from src.core.backtest.walkforward import run_walkforward  # varsa algo3'e düş

