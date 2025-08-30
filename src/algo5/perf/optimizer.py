import numpy as np

def fast_pnl(pos: np.ndarray, close: np.ndarray) -> np.ndarray:
    """
    Cumulative PnL vector with 1-bar delay:
    pnl[t] = pnl[t-1] + pos[t-1] * (close[t] - close[t-1]), pnl[0]=0
    """
    pos = np.asarray(pos, dtype=float)
    close = np.asarray(close, dtype=float)
    if pos.shape != close.shape:
        raise ValueError(f"pos and close shape mismatch: {pos.shape} vs {close.shape}")
    if close.size == 0:
        return np.array([], dtype=float)

    diffs = np.diff(close)              # length N-1
    contrib = pos[:-1] * diffs          # use previous-bar position
    out = np.empty_like(close, dtype=float)
    out[0] = 0.0
    out[1:] = np.cumsum(contrib)
    return out


def rolling_max_drawdown(equity: np.ndarray) -> float:
    """
    Max drawdown as negative number (e.g. -0.1234 for -12.34%).
    Accepts equity curve (not returns).
    """
    eq = np.asarray(equity, dtype=float)
    if eq.size == 0:
        return 0.0
    peaks = np.maximum.accumulate(eq)
    dd = (eq - peaks) / peaks
    return float(dd.min())
