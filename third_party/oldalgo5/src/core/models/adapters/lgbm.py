try:
    import lightgbm as lgb
except Exception as e:  # pragma: no cover
    raise

class LightGBMAdapter:
    def __init__(self, **kwargs):
        self.model = lgb.LGBMClassifier(
            n_estimators=kwargs.get("n_estimators", 200),
            learning_rate=kwargs.get("learning_rate", 0.05),
            subsample=kwargs.get("subsample", 0.9),
            colsample_bytree=kwargs.get("colsample_bytree", 0.9),
            random_state=kwargs.get("random_state", 42),
        )

    def fit(self, X, y):
        return self.model.fit(X, y)

    def predict_proba(self, X):
        return self.model.predict_proba(X)
