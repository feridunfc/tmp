
import os
import pytest
from pathlib import Path

store_mod = pytest.importorskip("algo5.data.feature_store.store")

def _mk_store(tmp_path):
    # prefer class FeatureStore(root=...)
    if hasattr(store_mod, "FeatureStore"):
        try:
            return store_mod.FeatureStore(root=tmp_path)
        except TypeError:
            return store_mod.FeatureStore(tmp_path)
    # fallbacks: module-level factory
    if hasattr(store_mod, "create_store"):
        return store_mod.create_store(tmp_path)
    pytest.skip("No FeatureStore available")

def _put(store, key, df):
    # prefer write
    for name in ("write", "save", "put"):
        if hasattr(store, name):
            return getattr(store, name)(key, df)
    pytest.skip("No write/save/put on FeatureStore")

def _get(store, key):
    for name in ("read", "load", "get"):
        if hasattr(store, name):
            return getattr(store, name)(key)
    pytest.skip("No read/load/get on FeatureStore")

def test_store_roundtrip(tmp_path, demo_df):
    st = _mk_store(tmp_path)
    key = "unit/test_roundtrip"
    _put(st, key, demo_df)
    read_df = _get(st, key)
    assert len(read_df) == len(demo_df)
    assert set(["Open","High","Low","Close","Volume"]).issubset(read_df.columns)

def test_overwrite(tmp_path, demo_df):
    st = _mk_store(tmp_path)
    key = "unit/overwrite"
    _put(st, key, demo_df.iloc[:50])
    _put(st, key, demo_df.iloc[:100])  # overwrite allowed
    out = _get(st, key)
    assert len(out) == 100
