import os
import pytest
from algo5.data.loader import demo_ohlcv

@pytest.fixture
def demo_df():
    periods = int(os.getenv("ALGO5_TEST_ROWS", "120"))
    return demo_ohlcv(periods=periods)
