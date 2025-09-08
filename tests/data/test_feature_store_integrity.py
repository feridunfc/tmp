from __future__ import annotations

import pandas as pd
import pytest

fs_mod = pytest.importorskip("algo5.data.feature_store.store")
FeatureStore = fs_mod.FeatureStore


def _mk_store(tmp_path):
    try:
        return FeatureStore(tmp_path)
    except TypeError:
        return FeatureStore(base_dir=tmp_path)


def test_upsert_is_idempotent(tmp_path):
    store = _mk_store(tmp_path)
    ts = pd.Timestamp("2024-01-01 10:00", tz="UTC")
    sym = "AAPL"
    feats = {"ma5": 10.0, "ma20": 9.5}
    r1 = store.upsert(sym, ts, feats)
    r2 = store.upsert(sym, ts, feats)
    rd = store.read(sym, ts)
    assert r1 == r2
    assert rd == feats
