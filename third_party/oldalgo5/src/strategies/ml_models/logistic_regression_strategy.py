from __future__ import annotations
import pandas as pd
import numpy as np
from typing import Dict, Any, Tuple
from sklearn.linear_model import LogisticRegression
from ..base_ml_strategy import BaseMLStrategy

class LogisticRegressionStrategy(BaseMLStrategy):
    NAME = "ml_logreg"

    def create_model(self, **params) -> LogisticRegression:
        defaults = dict(C=1.0, max_iter=1000, solver='lbfgs', n_jobs=None)
        defaults.update(params)
        return LogisticRegression(**defaults)

    def prepare_features(self, df: pd.DataFrame) -> Tuple[pd.DataFrame, pd.Series]:
        data = df.copy()
        close = data['Close'] if 'Close' in data.columns else data['close']
        data['ret'] = close.pct_change()
        data['mom_3'] = close.pct_change(3)
        data['mom_5'] = close.pct_change(5)
        data['vol_10'] = data['ret'].rolling(10).std()
        data['target'] = (close.shift(-1) > close).astype(int)
        data = data.replace([np.inf, -np.inf], np.nan).dropna()
        X = data[['ret','mom_3','mom_5','vol_10']]
        y = data['target']
        return X, y

    @staticmethod
    def schema() -> Dict[str, Any]:
        s = BaseMLStrategy.default_schema().copy()
        s.update({
            'C': {'type':'float','default':1.0,'min':0.01,'max':10.0,'step':0.1},
            'max_iter': {'type':'int','default':500,'min':100,'max':2000,'step':100},
        })
        return s
