import numpy as np
import pandas as pd
from algo5.engine.risk.chain import RiskChain
from algo5.engine.risk.rules import VolTargetRule
from algo5.engine.risk.sizer import Sizer


def test_chain_scales_down_on_high_vol():
    rets = pd.Series(np.r_[np.random.randn(100) * 0.001, np.random.randn(50) * 0.05])
    sig = pd.Series(1.0, index=rets.index)
    chain = RiskChain(Sizer(), [VolTargetRule(target_pct=15.0, lookback=20, ann=252)])
    w = chain.run(rets, sig)
    assert w.iloc[-1] < w.iloc[0]
