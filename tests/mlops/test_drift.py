
import pandas as pd
from algo5.mlops.drift import features_psi

def test_features_psi_basic():
    ref = pd.DataFrame({"x":[0,1,1,2,2,3,3,3], "y":[1,1,2,2,3,3,4,4]})
    cur = pd.DataFrame({"x":[3,3,2,2,1,1,0,0], "y":[4,4,3,3,2,2,1,1]})
    s = features_psi(ref, cur)
    assert set(s.index) == {"x","y"} and (s > 0).all()
