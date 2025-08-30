
import time
from algo5.mlops.registry import register, list_models, ModelMeta
import algo5.mlops.registry as reg

def test_registry_roundtrip(tmp_path, monkeypatch):
    monkeypatch.setattr(reg, "REGISTRY_FILE", tmp_path / "registry.json", raising=False)
    m = ModelMeta(name="clf", version="1", path="models/clf_v1.pkl", checksum="abc", created_ts=time.time())
    register(m)
    out = list_models("clf")["clf"]
    assert out and out[0]["version"] == "1"
