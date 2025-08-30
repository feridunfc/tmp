from __future__ import annotations
from dataclasses import dataclass
import pandas as pd

@dataclass
class WFConfig:
    n_splits: int = 3
    train_frac: float = 0.7

def time_series_windows(n_rows: int, cfg: WFConfig):
    """Basit expanding-window pencereleri.

    Her split'te train [0:train_end], val [train_end:val_end] verilir.
    """
    n = int(n_rows)
    start_train = max(1, int(n * cfg.train_frac))
    step = max(1, (n - start_train) // cfg.n_splits)
    for i in range(cfg.n_splits):
        train_end = start_train + i * step
        val_end = min(n, train_end + step)
        if val_end - train_end <= 0:
            break
        yield slice(0, train_end), slice(train_end, val_end)

def walk_forward(df: pd.DataFrame, eval_fn, params: dict, cfg: WFConfig):
    scores = []
    for tr, va in time_series_windows(len(df), cfg):
        df_win = df.iloc[:va.stop]  # train+val dilimi
        res = eval_fn(df_win, params)
        val = float(getattr(res, "acc", float("nan")))
        scores.append(val)
    return {
        "splits": len(scores),
        "acc_mean": float(pd.Series(scores).mean()) if scores else float("nan"),
        "acc_list": scores,
    }
