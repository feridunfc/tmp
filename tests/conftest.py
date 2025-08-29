import os, pytest
from algo5.data.loader import demo_ohlcv

@pytest.fixture
def demo_df():
    periods = int(os.getenv("ALGO5_TEST_ROWS", "120"))
    return demo_ohlcv(periods=periods)

@pytest.fixture(scope="session")
def _ensure_import_path():
    import sys
    from pathlib import Path
    root = Path(__file__).resolve().parents[1]
    if str(root) not in sys.path:
        sys.path.insert(0, str(root))
