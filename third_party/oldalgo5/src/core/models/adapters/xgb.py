try:
    import xgboost as xgb
except Exception as e:  # pragma: no cover
    raise

class XGBoostAdapter:
    def __init__(self, **kwargs):
        self.model = xgb.XGBClassifier(
            max_depth=kwargs.get("max_depth", 3),
            n_estimators=kwargs.get("n_estimators", 100),
            learning_rate=kwargs.get("learning_rate", 0.1),
            subsample=kwargs.get("subsample", 0.9),
            colsample_bytree=kwargs.get("colsample_bytree", 0.9),
            tree_method=kwargs.get("tree_method", "hist"),
            random_state=kwargs.get("random_state", 42),
        )

    def fit(self, X, y):
        return self.model.fit(X, y)

    def predict_proba(self, X):
        return self.model.predict_proba(X)
