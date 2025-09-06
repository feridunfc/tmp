from pathlib import Path
import sys, os
ROOT = Path(__file__).resolve().parents[1]
SRC = (ROOT / "src").resolve()
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))
os.environ["PYTHONPATH"] = str(SRC)
print("[i] SRC =", SRC)

from strategies.registry import bootstrap, get_registry

added = bootstrap("static")
REG, ORDER = get_registry()
print(f"[i] bootstrap added: {added}")
print(f"[i] registry size  : {len(REG)}")
print(f"[i] first entries  : {ORDER[:5]}")
if ORDER:
    k = ORDER[0][0]; v = REG[k]
    print(f"[i] sample key     : {k}")
    print(f"[i] has 'gen'      : {callable(v.get('gen'))}")
    print(f"[i] has 'prep'     : {callable(v.get('prep'))}")
    schema = v.get("schema") or {}
    print(f"[i] schema (len)   : {len(schema)}")
else:
    print("[!] ORDER empty. Check strategies package & static bindings.")
