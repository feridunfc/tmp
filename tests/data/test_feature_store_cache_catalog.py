from algo5.data.feature_store.cache import SmartCache, set_cache_root
from algo5.data.feature_store.catalog import list_namespaces, list_items

def test_smart_cache_roundtrip(tmp_path, monkeypatch):
    set_cache_root(tmp_path/'cache'); c = SmartCache(); c.set('raw','demo',{'rows':10}); assert c.get('raw','demo')['rows']==10

def test_catalog_lists(tmp_path, monkeypatch):
    root = tmp_path/'cache'; (root/'raw').mkdir(parents=True); (root/'raw'/'a.json').write_text('{}'); (root/'raw'/'b.parquet').write_text('x')
    set_cache_root(root); assert 'raw' in list_namespaces(); assert set(list_items('raw'))=={'a','b'}
