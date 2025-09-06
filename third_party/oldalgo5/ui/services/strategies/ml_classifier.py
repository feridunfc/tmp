import pandas as pd, pickle
from ui.services.strategies.base import BaseStrategy
from ui.services import features as F
from ui.services.paths import models_dir
class ML_Classifier(BaseStrategy):
    @classmethod
    def name(cls): return "ML Classifier (Proba>thr)"
    @classmethod
    def param_schema(cls): return {"model_name":{"type":"text","default":"latest.pkl","label":"Model file"},"proba_threshold":{"type":"float","min":0.1,"max":0.9,"step":0.05,"default":0.5,"label":"Proba Threshold"}}
    @classmethod
    def generate_signals(cls, df: pd.DataFrame, params: dict) -> pd.Series:
        path = models_dir()/str(params.get("model_name","latest.pkl"))
        if not path.exists(): return pd.Series(0, index=df.index)
        with open(path,"rb") as f: bundle = pickle.load(f)
        model=bundle["model"]; feats=bundle["features"]
        X=F.make_feature_frame(df)[feats].fillna(0.0); proba=model.predict_proba(X)[:,1]
        return (proba > float(params.get("proba_threshold",0.5))).astype(int)
