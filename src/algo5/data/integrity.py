# FROZEN: Do not modify public API or behavior without an approved RFC.

"""
ALGO5 Module: src/algo5/data/integrity.py

Purpose
-------
Deterministic checksums and reproducibility seed management for data pipelines.

Responsibilities
----------------
- Compute deterministic, cache-key-safe checksums for DataFrames.
- Provide platform-independent strategy seeds with simple persistence helpers.

Public API
----------
- df_checksum(df, *, method="fast", include_index=True) -> str
- Reproducibility(global_seed=0, strategy_seeds=None)
  - get_strategy_seed(name, *, persist=True) -> int
  - apply(numpy=True, python=True) -> None
  - to_dict() / from_dict(dict) -> Reproducibility

Maturity & Status
-----------------
Maturity: FROZEN
Rationale: Security-upgraded (SHA-256), stable API; only critical fixes allowed.
Owner: platform-core   Since: 2025-08-31   Last-Reviewed: 2025-08-31

Notes
-----
- "fast" mode uses pandas hashing + SHA-256 (very fast; may vary across pandas versions).
- "stable" mode serializes via Arrow IPC then SHA-256 (slower; cross-version/platform stable).
"""

from __future__ import annotations

import hashlib
from dataclasses import dataclass, field
from typing import Any, Dict, Optional

import pandas as pd


__all__ = ["df_checksum", "Reproducibility"]


def df_checksum(
    df: pd.DataFrame,
    *,
    method: str = "fast",
    include_index: bool = True,
    canonicalize: bool = True,
) -> str:
    """Return a deterministic checksum of `df` (SHA-256).

    - "fast": pandas hash_pandas_object + SHA-256
    - "stable": Arrow IPC serialize + SHA-256 (yavaş ama platform/sürüm stabil)
    - canonicalize: kolonları alfabetik, satırları index'e göre sırala (order-invariant)
    """
    if method == "stable":
        try:
            import pyarrow as pa  # type: ignore
            import pyarrow.ipc as ipc  # type: ignore

            table = pa.Table.from_pandas(df, preserve_index=include_index)
            sink = pa.BufferOutputStream()
            with ipc.RecordBatchStreamWriter(sink, table.schema) as writer:
                writer.write_table(table)
            data = sink.getvalue().to_pybytes()
            return hashlib.sha256(data).hexdigest()
        except Exception:
            pass  # fall back to fast

    if canonicalize:
        df = df.copy()
        df = df[df.columns.sort_values()]        # deterministik kolon sırası
        try:
            df = df.sort_index()                 # deterministik satır sırası
        except Exception:
            pass

    hashed = pd.util.hash_pandas_object(df, index=include_index).values.tobytes()
    return hashlib.sha256(hashed).hexdigest()



@dataclass
class Reproducibility:
    """Deterministic seeding utilities for experiments/backtests.

    Args:
        global_seed: Base seed applied to Python/NumPy/etc. and folded into strategy seeds.
        strategy_seeds: Optional precomputed per-strategy seeds.

    Public methods:
        - get_strategy_seed(name, persist=True): idempotent per-strategy seed.
        - apply(numpy=True, python=True): set RNG seeds for common libs.
        - to_dict()/from_dict(): persist/restore reproducibility state.
    """
    global_seed: int = 0
    strategy_seeds: Dict[str, int] = field(default_factory=dict)

    # ---- Seed calculation -------------------------------------------------

    def _calculate_seed(self, strategy_name: str) -> int:
        """Platform-independent seed derived from strategy name + global_seed.

        Uses SHA-256 over the UTF-8 name; takes first 4 bytes (little-endian) and
        combines with global_seed. The modulus keeps it in 32-bit signed range.
        """
        name_bytes = strategy_name.encode("utf-8")
        name_hash32 = int.from_bytes(
            hashlib.sha256(name_bytes).digest()[:4], byteorder="little", signed=False
        )
        return (name_hash32 + int(self.global_seed)) % (2**31 - 1)

    def get_strategy_seed(self, strategy_name: str, *, persist: bool = True) -> int:
        """Return a deterministic seed for `strategy_name` (optionally caching it)."""
        if strategy_name in self.strategy_seeds:
            return self.strategy_seeds[strategy_name]
        seed = self._calculate_seed(strategy_name)
        if persist:
            self.strategy_seeds[strategy_name] = seed
        return seed

    # ---- State & application ---------------------------------------------

    def apply(self, *, numpy: bool = True, python: bool = True) -> None:
        """Apply `global_seed` to common RNGs (best-effort)."""
        if python:
            import random
            random.seed(int(self.global_seed))
        if numpy:
            try:
                import numpy as np  # type: ignore
                np.random.seed(int(self.global_seed))
            except Exception:
                pass
        # Optional: Torch if present
        try:
            import torch  # type: ignore
            torch.manual_seed(int(self.global_seed))
            if torch.cuda.is_available():
                torch.cuda.manual_seed_all(int(self.global_seed))
        except Exception:
            pass

    def to_dict(self) -> Dict[str, Any]:
        """Serialize reproducibility state (for reports/audit trails)."""
        return {
            "global_seed": int(self.global_seed),
            "strategy_seeds": dict(self.strategy_seeds),
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> "Reproducibility":
        """Restore reproducibility state from a dict."""
        return cls(
            global_seed=int(data.get("global_seed", 0)),
            strategy_seeds=dict(data.get("strategy_seeds", {})),
        )
