
import numpy as np, pandas as pd
from algo5.explain.permutation import permutation_importance

class Lin:
    def __init__(self, w): self.w = np.asarray(w)
    def predict(self, X): Xn = np.asarray(X); return Xn @ self.w

def test_perm_ordering():
    rng = np.random.default_rng(7)
    X = pd.DataFrame(rng.normal(size=(200,3)), columns=["x1","x2","x3"])
    y = 2*X["x1"] - 1*X["x2"] + rng.normal(0,0.1, size=200)
    m = Lin([2.0, -1.0, 0.0])
    imp = permutation_importance(m, X, y.to_numpy(), n_repeats=3)
    assert imp.index[0] == "x1" and imp.index[1] == "x2"
