from __future__ import annotations
import numpy as np
import pandas as pd


def block_bootstrap_returns(
    returns: pd.Series,
    *,
    block: int = 5,
    n: int | None = None,
    seed: int | None = None,
) -> pd.Series:
    """
    Basit block-bootstrap: returns içinden uzunluğu `block` olan blokları
    rastgele seçip peş peşe koyarak uzunluğu `n` olan yeni seri üretir.
    - Deterministik olması için `seed` -> np.random.RandomState(seed)
    - Çıkış index'i her zaman RangeIndex(0..n-1)
    """
    if n is None:
        n = len(returns)
    if block < 1:
        raise ValueError("block must be >= 1")

    vals = returns.to_numpy()
    rng = np.random.RandomState(seed) if seed is not None else np.random.RandomState()

    out = np.empty(n, dtype=float)
    i = 0
    # Başlangıç konumu için üst sınır (blok taşmayacak şekilde)
    max_start = max(0, len(vals) - block)

    while i < n:
        start = rng.randint(0, max_start + 1) if max_start > 0 else 0
        chunk = vals[start : start + block]
        take = min(block, n - i)
        out[i : i + take] = chunk[:take]
        i += take

    # n uzunluğunda düz (0..n-1) indeksle döndür
    return pd.Series(out, index=pd.RangeIndex(n), name="ret_boot")
