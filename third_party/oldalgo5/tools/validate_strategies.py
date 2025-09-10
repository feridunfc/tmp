from __future__ import annotations
from pathlib import Path
import sys, os
import pandas as pd
import numpy as np

ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "src").resolve()
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
os.environ["PYTHONPATH"] = str(SRC)

from strategies.registry import bootstrap, list_strategies, get_strategy

def toy_df(n=240, seed=42):
    rng = np.random.default_rng(seed)
    idx = pd.date_range("2022-01-01", periods=n, freq="D")
    close = 100 + rng.standard_normal(n).cumsum()
    return pd.DataFrame({
        "Open": close + rng.normal(0, 0.1, n),
        "High": close + np.abs(rng.normal(0, 0.5, n)),
        "Low":  close - np.abs(rng.normal(0, 0.5, n)),
        "Close": close,
        "Volume": 1000 + rng.integers(0, 500, n)
    }, index=idx)

def defaults(schema: dict) -> dict:
    out = {}
    for k, spec in (schema or {}).items():
        if isinstance(spec, dict) and "default" in spec:
            out[k] = spec["default"]
    return out

if __name__ == "__main__":
    bootstrap("static")
    names = list_strategies()
    if not names:
        print("❌ Registry boş.")
        raise SystemExit(2)

    df = toy_df()
    ok = 0; fail = 0
    for name in names:
        try:
            s = get_strategy(name)
            params = defaults(getattr(s, "schema", {}))
            d2 = s.prepare(df.copy(), **params)
            sig = s.generate_signals(d2.copy(), **params)

            assert len(sig) == len(d2), "len mismatch"
            assert not sig.isna().any(), "NaN in signals"

            print(f"✅ {name} OK")
            ok += 1
        except Exception as e:
            print(f"❌ {name}", e)
            fail += 1
    print(f"\nSummary: OK={ok} FAIL={fail}")
    if fail:
        raise SystemExit(1)
