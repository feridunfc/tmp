
from algo5.mlops.ab_test import EpsilonGreedy

def test_eps_greedy_updates():
    eg = EpsilonGreedy(["A","B"], eps=0.0, seed=1)
    a = eg.select(); assert a == "A"
    eg.update("A", 1.0)
    assert eg.select() == "A"
    eg.update("B", 2.0)
    eg.eps = 1.0
    assert eg.select() in ("A","B")
