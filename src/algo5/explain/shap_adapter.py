
from __future__ import annotations
import pandas as pd
try:
    import shap  # type: ignore
except Exception:
    shap = None
from .permutation import permutation_importance

def explain(model, X: pd.DataFrame, y=None):
    if shap is None:
        return {"method": "permutation", "values": permutation_importance(model, X, y if y is not None else X.iloc[:,0]*0)}
    try:
        explainer = shap.Explainer(model.predict, X)
        sv = explainer(X)
        import numpy as np
        vals = abs(sv.values).mean(0)
        return {"method":"shap", "values": pd.Series(vals, index=X.columns).sort_values(ascending=False)}
    except Exception:
        return {"method": "permutation", "values": permutation_importance(model, X, y if y is not None else X.iloc[:,0]*0)}
