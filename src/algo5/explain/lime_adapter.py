
from __future__ import annotations
import pandas as pd
try:
    from lime.lime_tabular import LimeTabularExplainer  # type: ignore
except Exception:
    LimeTabularExplainer = None

def explain_sample(model, X: pd.DataFrame, row: int = 0):
    if LimeTabularExplainer is None:
        return {"method":"none", "values": None}
    expl = LimeTabularExplainer(X.to_numpy(), feature_names=X.columns, discretize_continuous=True)
    exp = expl.explain_instance(X.iloc[row].to_numpy(), model.predict)
    return {"method":"lime", "values": exp.as_list()}
