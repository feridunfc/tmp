import pandas as pd, pickle
from sklearn.ensemble import RandomForestClassifier
from sklearn.linear_model import LogisticRegression
from sklearn.model_selection import train_test_split
from sklearn.metrics import roc_auc_score, accuracy_score
from ui.services import features as F
from ui.services.paths import models_dir
def create_features_and_labels(df: pd.DataFrame, horizon:int=1, threshold:float=0.0):
    X = F.make_feature_frame(df); y = F.make_labels(df, horizon=horizon, threshold=threshold).reindex(X.index).fillna(0).astype(int); return X.fillna(0.0), y
def train_model(df: pd.DataFrame, *, algo:str="rf", params:dict=None, horizon:int=1, threshold:float=0.0):
    params = params or {}; X,y = create_features_and_labels(df, horizon=horizon, threshold=threshold)
    Xtr, Xte, ytr, yte = train_test_split(X, y, test_size=0.3, shuffle=False)
    if algo=="rf":
        model = RandomForestClassifier(n_estimators=int(params.get("n_estimators",200)), max_depth=int(params.get("max_depth",5)), random_state=42, n_jobs=-1)
    else:
        model = LogisticRegression(max_iter=1000)
    model.fit(Xtr, ytr); proba = model.predict_proba(Xte)[:,1]
    auc = roc_auc_score(yte, proba) if len(set(yte))>1 else 0.5; acc = accuracy_score(yte, (proba>0.5).astype(int))
    return model, {"auc":float(auc),"acc":float(acc)}, list(X.columns)
def save_model(model, feat_names, name:str="latest.pkl"):
    path = models_dir()/name
    with open(path,"wb") as f: pickle.dump({"model":model,"features":feat_names}, f)
    return path
