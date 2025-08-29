from __future__ import annotations

from pathlib import Path

import pandas as pd

from algo5.data.feature_store.store import FeatureStore
from algo5.data.feature_store.cache import set_cache_root


def _mk_store(tmp_path: Path) -> FeatureStore:
    set_cache_root(tmp_path)
    return FeatureStore()


def _put(store: FeatureStore, key: str, df: pd.DataFrame):
    for name in ("save", "write", "put"):
        if hasattr(store, name):
            return getattr(store, name)(key, df)
    raise AttributeError("no save/write/put on store")


def _get(store: FeatureStore, key: str | tuple[str, str]) -> pd.DataFrame:
    for name in ("load", "read", "get"):
        if hasattr(store, name):
            return getattr(store, name)(key)
    raise AttributeError("no load/read/get on store")


def test_store_roundtrip(tmp_path, demo_df):
    st = _mk_store(tmp_path)
    key = "unit/test_roundtrip"
    _put(st, key, demo_df)
    out = _get(st, key)
    assert len(out) == len(demo_df)
    assert list(out.columns) == list(demo_df.columns)


def test_overwrite(tmp_path, demo_df):
    st = _mk_store(tmp_path)
    key = "unit/overwrite"
    _put(st, key, demo_df.iloc[:50])
    st.save(("raw", key), demo_df.iloc[:100], overwrite=True)
    out = _get(st, ("raw", key))
    assert len(out) == 100
