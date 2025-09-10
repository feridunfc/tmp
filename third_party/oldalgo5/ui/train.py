# ui/train.py
from services import sdk
import itertools, json
from pathlib import Path
import pandas as pd

def run(state):
    """
    Basit HPO (grid search): MA Fast/Slow taraması.
    Sonuç: en iyi Sharpe (+CAGR tie-break) ve artifacts kaydı.
    """
    if "data" not in state:
        return {"error": "Data yok. Önce Data sekmesinden veri yükleyin."}

    data = state["data"]
    commission = float(state.get("commission_bps", 5.0)) / 10000.0
    slippage  = float(state.get("slippage_bps", 10.0)) / 10000.0

    # Grid: istersen streamlit'te state'e yazarak değiştirilebilir
    fast_grid = state.get("train_fast_grid", [5, 10, 15, 20])
    slow_grid = state.get("train_slow_grid", [20, 30, 50, 100])

    rows = []
    best = None
    best_key = None

    for f, s in itertools.product(fast_grid, slow_grid):
        if f >= s:
            continue  # mantıksız kombinasyonu atla
        _, metrics = sdk.run_backtest(
            data, commission=commission, slippage=slippage, fast=int(f), slow=int(s)
        )
        sharpe = float(metrics["Sharpe"].mean())
        cagr   = float(metrics["CAGR"].mean())
        row = {
            "Fast": int(f), "Slow": int(s),
            "Sharpe": sharpe, "CAGR": cagr,
            "MaxDD": float(metrics["MaxDD"].mean()),
            "AnnReturn": float(metrics["AnnReturn"].mean()),
        }
        rows.append(row)
        key = (sharpe, cagr)
        if (best_key is None) or (key > best_key):
            best_key = key
            best = row

    grid_df = pd.DataFrame(rows).sort_values(["Sharpe", "CAGR"], ascending=[False, False])

    # En iyi parametreleri state'e ve diske yaz
    state["best_params"] = {"fast": int(best["Fast"]), "slow": int(best["Slow"])}
    state["last_hpo"] = grid_df

    art_dir = Path(__file__).parent / "artifacts"
    art_dir.mkdir(exist_ok=True)
    grid_df.to_csv(art_dir / "grid_results.csv", index=False)
    with open(art_dir / "best_params.json", "w", encoding="utf-8") as f:
        json.dump(state["best_params"], f, indent=2)

    return {
        "message": "Training (grid search) tamamlandı.",
        "best_params": state["best_params"],
        "top5": grid_df.head(5).to_dict(orient="records"),
        "artifacts": {
            "grid_csv": str(art_dir / "grid_results.csv"),
            "best_json": str(art_dir / "best_params.json"),
        },
    }
