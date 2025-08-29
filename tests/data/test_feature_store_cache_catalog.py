import os
from pathlib import Path
from algo5.data.feature_store.cache import SmartCache
from algo5.data.feature_store.catalog import list_namespaces, list_items

def test_smart_cache_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setenv("ALGO5_CACHE_ROOT", str(tmp_path / "cache"))
    c = SmartCache()
    c.set("raw", "demo", {"rows": 10})
    got = c.get("raw", "demo")
    assert got["rows"] == 10

def test_catalog_lists(tmp_path, monkeypatch):
    root = tmp_path / "cache"
    (root / "raw").mkdir(parents=True)
    (root / "raw" / "a.json").write_text("{}", encoding="utf-8")
    (root / "raw" / "b.parquet").write_text("x", encoding="utf-8")
    monkeypatch.setenv("ALGO5_CACHE_ROOT", str(root))
    ns = list_namespaces()
    assert "raw" in ns
    items = list_items("raw")
    assert set(items) == {"a", "b"}
