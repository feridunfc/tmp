from sklearn.ensemble import RandomForestClassifier

class RandomForestAdapter:
    def __init__(self, **kwargs):
        self.model = RandomForestClassifier(n_estimators=kwargs.get("n_estimators", 100),
                                            random_state=kwargs.get("random_state", 42))

    def fit(self, X, y):
        return self.model.fit(X, y)

    def predict_proba(self, X):
        if hasattr(self.model, "predict_proba"):
            return self.model.predict_proba(X)
        # Fallback: binary decision to proba-ish
        pred = self.model.predict(X)
        import numpy as np
        return np.vstack([1-pred, pred]).T
