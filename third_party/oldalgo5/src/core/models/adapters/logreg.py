from sklearn.linear_model import LogisticRegression

class LogRegAdapter:
    def __init__(self, **kwargs):
        self.model = LogisticRegression(max_iter=kwargs.get("max_iter", 1000))

    def fit(self, X, y):
        return self.model.fit(X, y)

    def predict_proba(self, X):
        return self.model.predict_proba(X)
