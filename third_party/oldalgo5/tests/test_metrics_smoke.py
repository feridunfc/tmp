import numpy as np
import pandas as pd
from src.utils.metrics import calculate_metrics

def test_calculate_metrics_basic():
    ret = pd.Series(np.random.randn(300)*0.001)
    eq = (1+ret).cumprod()*10000
    m = calculate_metrics(eq, ret)
    for k in ["sharpe","max_drawdown","total_return","calmar"]:
        assert k in m
