import numpy as np
from algo5.perf.optimizer import fast_pnl, rolling_max_drawdown
def test_fast_pnl_and_dd():
    close = np.array([100,101,102,101,103,104], float); pos = np.array([0,1,1,0,1,1], float)
    pnl = fast_pnl(pos, close)
    naive = [0.0]
    for t in range(1,len(close)): naive.append(naive[-1]+pos[t-1]*(close[t]-close[t-1]))
    import numpy as _np
    naive = _np.array(naive)
    assert (abs(pnl-naive) < 1e-9).all()
    eq = 100 + pnl; dd = rolling_max_drawdown(eq); assert dd <= 0.0
