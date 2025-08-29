from pathlib import Path

def _put(store, key, df):
    # try common API names
    for name in ("write", "save", "put"):
        if hasattr(store, name):
            return getattr(store, name)(key, df)

def _get(store, key):
    for name in ("read", "get", "load"):
        if hasattr(store, name):
            return getattr(store, name)(key)

def _mk_store(tmp_path: Path):
    from algo5.data.feature_store.store import FeatureStore
    return FeatureStore(root=tmp_path)

def test_store_roundtrip(tmp_path, demo_df):
    st = _mk_store(tmp_path)
    key = "unit/test_roundtrip"
    _put(st, key, demo_df)
    out = _get(st, key)
    assert out.equals(demo_df)

def test_overwrite(tmp_path, demo_df):
    st = _mk_store(tmp_path)
    key = "unit/overwrite"
    _put(st, key, demo_df.iloc[:50])
    _put(st, key, demo_df.iloc[:100])  # overwrite allowed
    out = _get(st, key)
    assert len(out) == 100
