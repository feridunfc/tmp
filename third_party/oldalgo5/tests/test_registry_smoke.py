import os, sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "src").resolve()
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
os.environ["PYTHONPATH"] = str(SRC)

from strategies.registry import bootstrap, get_registry

def test_registry_smoke():
    bootstrap("both")
    REG, ORDER = get_registry()
    assert isinstance(REG, dict) and isinstance(ORDER, list)
    if ORDER:
        k, label = ORDER[0]
        assert k in REG
        entry = REG[k]
        assert callable(entry["gen"])
        assert entry.get("prep") is None or callable(entry["prep"])
