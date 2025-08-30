
from algo5.data.loader import demo_ohlcv
from algo5.features.regime.voltrend import make_regime_features

def test_voltrend_shapes():
    df = demo_ohlcv(periods=120)
    f = make_regime_features(df)
    assert {"ret","rv_5","rv_10","rv_20","mom_5","mom_10","mom_20","zvol"} <= set(f.columns)
    assert len(f) == len(df)
