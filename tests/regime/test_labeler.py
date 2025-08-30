
from algo5.data.loader import demo_ohlcv
from algo5.features.regime.voltrend import make_regime_features
from algo5.models.regime.labeler import label_by_vol_zscore

def test_labeler_length_range():
    feats = make_regime_features(demo_ohlcv(200))
    lab = label_by_vol_zscore(feats, n_states=3, seed=7)
    assert len(lab) == len(feats)
    assert set(lab.unique()) <= {0,1,2}
