"""Robustness/stress modules: jitter, worst-days, Monte Carlo bootstrap."""
from .jitter import jitter_returns
from .worst_days import remove_best_k_days, remove_worst_k_days
from .mc import block_bootstrap_returns
__all__ = [
    "jitter_returns", "remove_best_k_days", "remove_worst_k_days", "block_bootstrap_returns"
]
