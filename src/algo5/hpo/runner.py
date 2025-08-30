from __future__ import annotations
import itertools
import pandas as pd

def _param_grid(space: dict):
    keys = list(space.keys())
    for values in itertools.product(*(space[k] for k in keys)):
        yield dict(zip(keys, values))

def grid_search(df, space, eval_fn, *, metric: str = "acc"):
    records = []
    best = None
    best_val = float("-inf")
    for params in _param_grid(space):
        res = eval_fn(df, params)
        val = float(getattr(res, metric, float("nan")) if hasattr(res, metric) else res.get(metric, float("nan")))
        rec = {"metric": metric, metric: val, "params": params}
        records.append(rec)
        if val > best_val:
            best_val = val
            best = params
    return pd.DataFrame(records).sort_values(metric, ascending=False, ignore_index=True), best
