
from algo5.data.loader import demo_ohlcv
from algo5.features.regime.voltrend import make_regime_features
from algo5.models.regime.labeler import label_by_vol_zscore
from algo5.strategies.hybrid.regime_aware import regime_aware_position

def test_positions_len_and_bounds():
    df = demo_ohlcv(150)
    feats = make_regime_features(df)
    lab = label_by_vol_zscore(feats, 3, 42)
    pos = regime_aware_position(df["Close"], lab)
    assert len(pos) == len(df)
    assert pos.min() >= 0.0 and pos.max() <= 1.0
