
import os, sys
from pathlib import Path
import numpy as np
import pandas as pd
import pytest

@pytest.fixture(autouse=True, scope="session")
def _ensure_import_path():
    # add <repo>/src to sys.path if present
    repo_root = Path(__file__).resolve().parents[1]
    src = repo_root / "src"
    if src.exists():
        sys.path.insert(0, str(src))

@pytest.fixture(autouse=True)
def _seed():
    # deterministic numpy seed for each test
    np.random.seed(123)

@pytest.fixture
def _cache_root(tmp_path, monkeypatch):
    # function-scoped to be compatible with monkeypatch fixture
    cache_root = tmp_path / ".cache" / "features"
    cache_root.mkdir(parents=True, exist_ok=True)
    monkeypatch.setenv("ALGO5_CACHE_ROOT", str(cache_root))
    return cache_root


@pytest.fixture
def demo_df():
    periods = int(os.getenv("ALGO5_TEST_ROWS", "120"))
    idx = pd.date_range("2024-01-01", periods=periods, freq="D")
    base = np.arange(periods, dtype=float)
    df = pd.DataFrame(
        {
            "Open":  100 + base - 1,
            "High":  100 + base + 1,
            "Low":   100 + base - 2,
            "Close": 100 + base,
            "Volume": 1000 + np.arange(periods, dtype=int),
        },
        index=idx,
    )
    return df