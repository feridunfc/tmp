"""
ALGO5 Module: src/algo5/data/loader.py

Purpose
-------
Generate synthetic OHLCV demo frames (UTC-safe) for diagnostics, UI demos,
and stress testing. Includes ESG proxy and common market scenarios.

Responsibilities
----------------
- Produce deterministic, UTC-indexed OHLCV data for demos/tests.
- Provide simple scenario generators (bull/bear/sideways/gap/vol-spike).
- Include an ESG proxy column compatible with Week-1 DQ/monitoring.

Public API
----------
- demo_ohlcv(periods=120, tz="UTC", seed=None, drift=0.0, sigma=1.0, esg_per_tick=0.04)
- bull_market_demo(periods=120, tz="UTC", seed=None)
- bear_market_demo(periods=120, tz="UTC", seed=None)
- sideways_market_demo(periods=120, tz="UTC", seed=None)
- gap_down_demo(periods=120, tz="UTC", seed=None, gap_bps=500)
- volatility_spike_demo(periods=120, tz="UTC", seed=None, spike_at=60, spike_sigma=4.0)

Maturity & Status
-----------------
Maturity: STABLE
Rationale: Aligned with 2025-ready validator (columns/dtypes/UTC); extendable.
Owner: data-platform   Since: 2025-08-31   Last-Reviewed: 2025-08-31

Notes
-----
- Columns are canonical: "Open","High","Low","Close","volume" (+ "co2e_per_tick").
- ESG proxy is a simple placeholder (0.04 g per tick); validator aggregates as needed.
"""

from __future__ import annotations
from typing import Optional
import numpy as np
import pandas as pd


def _utc_index(periods: int, tz: str = "UTC", freq: str = "D") -> pd.DatetimeIndex:
    """Return a timezone-aware (UTC by default) DatetimeIndex."""
    # use 'min' instead of deprecated 'T' where minutes are needed
    return pd.date_range("2024-01-01", periods=periods, tz=tz, freq=freq)


def _path(periods: int, *, seed: Optional[int], drift: float, sigma: float, start: float = 100.0) -> np.ndarray:
    """Simple additive random walk with drift (deterministic via seed)."""
    rng = np.random.default_rng(seed)
    steps = drift + rng.normal(0.0, sigma, size=periods)
    series = start + np.cumsum(steps)
    return series


def _ohlcv_from_close(close: np.ndarray, *, rng: np.random.Generator, spread: float = 1.0) -> tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    """Derive Open/High/Low from Close with a tiny, realistic spread."""
    # Prev close as open; first open ~ first close
    open_ = np.empty_like(close)
    open_[0] = close[0]
    open_[1:] = close[:-1]

    # High/Low add mild intra-bar variation
    noise = rng.normal(0.0, 0.15 * spread, size=close.size)
    high = np.maximum.reduce([open_, close, (open_ + close) / 2 + spread + noise])
    low  = np.minimum.reduce([open_, close, (open_ + close) / 2 - spread - noise])

    return open_, high, low, close


def demo_ohlcv(
    periods: int = 120,
    tz: str = "UTC",
    seed: int | None = None,
    drift: float = 0.0,
    sigma: float = 1.0,
    esg_per_tick: float = 0.04,  # grams CO2e per tick (placeholder)
) -> pd.DataFrame:
    """Generate synthetic OHLCV demo data (UTC-safe, 2025-ready).

    Args:
        periods: Number of rows.
        tz: Timezone (kept UTC by default; validator expects UTC).
        seed: RNG seed for determinism.
        drift: Per-step drift of the random walk (e.g., 0.05 for gentle uptrend).
        sigma: Step volatility (standard deviation).
        esg_per_tick: ESG proxy in grams CO2e per tick.

    Returns:
        DataFrame with columns: Open, High, Low, Close, volume, co2e_per_tick.
        Index is tz-aware (UTC by default).
    """
    idx = _utc_index(periods, tz=tz, freq="D")
    rng = np.random.default_rng(seed)

    close = _path(periods, seed=seed, drift=drift, sigma=sigma, start=100.0)
    open_, high, low, close = _ohlcv_from_close(close, rng=rng, spread=1.0)

    # simple increasing volume with small noise
    volume = (1000 + np.arange(periods)).astype("int64") + rng.integers(-10, 10, size=periods)

    df = pd.DataFrame(
        {
            "Open": open_.astype("float64"),
            "High": high.astype("float64"),
            "Low":  low.astype("float64"),
            "Close": close.astype("float64"),
            "volume": volume,                 # NOTE: lower-case to match validator/schemas
            "co2e_per_tick": float(esg_per_tick),
        },
        index=idx,
    )
    return df


# -------- Market scenarios -------------------------------------------------------

def bull_market_demo(periods: int = 120, tz: str = "UTC", seed: int | None = None) -> pd.DataFrame:
    """Uptrend scenario with mild volatility."""
    return demo_ohlcv(periods=periods, tz=tz, seed=seed, drift=+0.20, sigma=0.8)


def bear_market_demo(periods: int = 120, tz: str = "UTC", seed: int | None = None) -> pd.DataFrame:
    """Downtrend scenario with mild volatility."""
    return demo_ohlcv(periods=periods, tz=tz, seed=seed, drift=-0.20, sigma=0.8)


def sideways_market_demo(periods: int = 120, tz: str = "UTC", seed: int | None = None) -> pd.DataFrame:
    """Sideways/chop scenario with low volatility."""
    return demo_ohlcv(periods=periods, tz=tz, seed=seed, drift=0.0, sigma=0.3)


def gap_down_demo(
    periods: int = 120,
    tz: str = "UTC",
    seed: int | None = None,
    gap_bps: int = 500,   # 500 bps = -5% one-time gap at t=periods//3
) -> pd.DataFrame:
    """Single large negative gap, useful for stress tests."""
    df = demo_ohlcv(periods=periods, tz=tz, seed=seed, drift=0.0, sigma=0.8)
    t = max(1, periods // 3)
    factor = 1.0 - (gap_bps / 10_000.0)
    df.iloc[t:, df.columns.get_indexer(["Open", "High", "Low", "Close"])] *= factor
    return df


def volatility_spike_demo(
    periods: int = 120,
    tz: str = "UTC",
    seed: int | None = None,
    spike_at: int = 60,
    spike_sigma: float = 4.0,
) -> pd.DataFrame:
    """Volatility regime change mid-series."""
    # first half calm, second half volatile
    half = max(1, min(periods - 1, spike_at))
    df_a = demo_ohlcv(periods=half, tz=tz, seed=seed, drift=0.0, sigma=0.4)
    df_b = demo_ohlcv(periods=periods - half, tz=tz, seed=None if seed is None else seed + 1, drift=0.0, sigma=spike_sigma)
    # stitch B after A with continuity at boundary
    shift = df_a["Close"].iloc[-1] - df_b["Open"].iloc[0]
    df_b.loc[:, ["Open", "High", "Low", "Close"]] = df_b[["Open", "High", "Low", "Close"]] + float(shift)
    return pd.concat([df_a, df_b])
