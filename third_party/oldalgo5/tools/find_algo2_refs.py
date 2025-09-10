# tools/patch_algo2_imports.py
from __future__ import annotations
from pathlib import Path
import re

ROOT = Path(__file__).resolve().parents[1]
SRC = ROOT / "src"

# Genel eşlemeler
RE_MAP = [
    (r"\balgo2\.core\.strategies\.", "strategies."),
    (r"\balgo2\.core\.backtest\.",   "core.backtest."),
    (r"\balgo2\.core\.risk\.",       "core.risk."),
    (r"\balgo2\.core\.features\.",   "core.features."),
    (r"\balgo2\.core\.anomaly\.",    "core.anomaly."),
    (r"\balgo2\.utils\.",            "utils."),
    (r"\balgo2\.signal\.",           "app_signals."),
    (r"\balgo2\.nlp\.",              "nlp."),
    (r"\balgo2\.anomaly\.",          "anomaly."),
]

# Özel durumlar (tam eşleşme)
LITERAL_MAP = {
    "from algo2.core.models.registry import get_model, list_models":
        "from strategies.ml_models.registry import get_model, list_models",
    "from algo2.backtest.simple import run_backtest_from_signals":
        "from core.backtest.simple import run_backtest_from_signals",
}

def patch_text(s: str) -> str:
    for k, v in LITERAL_MAP.items():
        s = s.replace(k, v)
    for pat, repl in RE_MAP:
        s = re.sub(pat, repl, s)
    return s

def main():
    changed = 0
    for py in SRC.rglob("*.py"):
        if "__pycache__" in py.parts:
            continue
        t = py.read_text(encoding="utf-8", errors="ignore")
        nt = patch_text(t)
        if nt != t:
            py.write_text(nt, encoding="utf-8")
            changed += 1
            print(f"[+] {py}")
    print(f"[✓] Değiştirilen dosya: {changed}")

if __name__ == "__main__":
    main()
