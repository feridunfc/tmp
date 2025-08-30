from algo5.data.loader import demo_ohlcv
from algo5.hpo.space import default_space
from algo5.hpo.runner import grid_search
from algo5.train.runner import train_eval_simple

def test_grid_search_returns_best():
    df = demo_ohlcv(160)
    space = default_space()
    table, best = grid_search(df, space, lambda d, p: train_eval_simple(d, p))
    assert not table.empty
    assert isinstance(best, dict) and "window" in best and "threshold" in best
