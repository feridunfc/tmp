from algo5.data.feature_store.store import FeatureStore
from algo5.data.feature_store.cache import set_cache_root

def _mk_store(tmp_path): set_cache_root(tmp_path); return FeatureStore()

def test_store_roundtrip(tmp_path, demo_df):
    st = _mk_store(tmp_path); st.save('unit/rt', demo_df, overwrite=True); out = st.load('unit/rt'); assert len(out)==len(demo_df)

def test_overwrite(tmp_path, demo_df):
    st = _mk_store(tmp_path); st.save('unit/x', demo_df.iloc[:50], overwrite=True); st.save('unit/x', demo_df.iloc[:100], overwrite=True); out = st.load('unit/x'); assert len(out)==100
