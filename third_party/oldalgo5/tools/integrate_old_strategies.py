import shutil, pathlib, re, sys, time

# --- Ayarlar ---
PROJECT_ROOT = pathlib.Path(__file__).resolve().parents[1]   # tools/.. -> proje kökü
SRC = PROJECT_ROOT / "src"
OLD = SRC / "core" / "strategies"
NEW = SRC / "strategies"

# Eski çekirdekteki gelişkin tekil dosyalar (var olanları alır)
CORE_FILES = [
    "registry.py", "base.py", "utils.py", "adapters.py",
    "ai_unified.py", "field_spec.py", "hybrid_ensemble.py",
    "ma_crossover.py", "xgboost_strategy.py", "registry_ext.py"
]

# Dizin eşlemeleri: eski -> yeni
DIR_MAP = {
    "rule_based": "rule",
    "ai": "ai",
    "hybrid": "hybrid",
    "plugins": "plugins",
    "conventional": "conventional",
    "ensemble": "ensemble",
}

# Import düzenleme kalıpları
PATTERNS = [
    # algo2 -> strategies
    (re.compile(r"\bfrom\s+algo2\.strategies\b"), "from strategies"),
    (re.compile(r"\bimport\s+algo2\.strategies\b"), "import strategies"),
    (re.compile(r"\bfrom\s+algo2\.strategies\."), "from strategies."),
    (re.compile(r"\bimport\s+algo2\.strategies\."), "import strategies."),

    # core.strategies -> strategies (genel)
    (re.compile(r"\bfrom\s+core\.strategies\b"), "from strategies"),
    (re.compile(r"\bimport\s+core\.strategies\b"), "import strategies"),
    (re.compile(r"\bfrom\s+core\.strategies\."), "from strategies."),
    (re.compile(r"\bimport\s+core\.strategies\."), "import strategies."),

    # rule_based alt yolu -> rule
    (re.compile(r"\bfrom\s+strategies\.rule_based\b"), "from strategies.rule"),
    (re.compile(r"\bimport\s+strategies\.rule_based\b"), "import strategies.rule"),
    (re.compile(r"\bfrom\s+strategies\.rule_based\."), "from strategies.rule."),
    (re.compile(r"\bimport\s+strategies\.rule_based\."), "import strategies.rule."),
]

IGNORE_DIR_NAMES = {"__pycache__", ".venv", ".git", ".idea", "site-packages"}

def backup_dir():
    stamp = time.strftime("%Y%m%d_%H%M%S")
    bdir = PROJECT_ROOT / f"migration_backup_{stamp}"
    bdir.mkdir(parents=True, exist_ok=True)
    return bdir

def safe_copy(src: pathlib.Path, dst: pathlib.Path, bdir: pathlib.Path):
    dst.parent.mkdir(parents=True, exist_ok=True)
    if dst.exists():
        rel = dst.relative_to(PROJECT_ROOT)
        bak = bdir / rel
        bak.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(dst, bak)
    shutil.copy2(src, dst)

def merge_dir(old_dir: pathlib.Path, new_dir: pathlib.Path, bdir: pathlib.Path):
    if not old_dir.exists():
        return []
    moved = []
    for p in old_dir.rglob("*"):
        if p.is_dir():
            continue
        rel = p.relative_to(old_dir)
        dst = new_dir / rel
        safe_copy(p, dst, bdir)
        moved.append((p, dst))
    # __init__.py yoksa ekleyelim
    for d in [new_dir, *[x for x in new_dir.rglob("*") if x.is_dir()]]:
        init = d / "__init__.py"
        if not init.exists():
            init.write_text("", encoding="utf-8")
    return moved

def write_file(path: pathlib.Path, content: str, bdir: pathlib.Path):
    if path.exists():
        bak = bdir / path.relative_to(PROJECT_ROOT)
        bak.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, bak)
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(content, encoding="utf-8")

def make_shims(bdir: pathlib.Path):
    """src/core/strategies altında uyumluluk shims"""
    init_shim = '''\
import warnings as _w, importlib as _il
_w.warn("Importing from 'core.strategies' is deprecated. Use 'strategies'.",
        DeprecationWarning, stacklevel=2)
_mod = _il.import_module("strategies")
globals().update({k: v for k, v in _mod.__dict__.items() if not k.startswith("_")})
'''
    module_shim = '''\
from importlib import import_module as _im
_mod = _im("strategies.{TARGET}")
globals().update({k: v for k, v in _mod.__dict__.items() if not k.startswith("_")})
'''

    write_file(OLD / "__init__.py", init_shim, bdir)
    for name in {"registry", "base", "utils", "adapters", "ai_unified", "field_spec"}:
        write_file(OLD / f"{name}.py", module_shim.replace("{TARGET}", name), bdir)

def ensure_new_init(bdir: pathlib.Path):
    """strategies/__init__.py içine temel exportları yerleştir."""
    target = NEW / "__init__.py"
    content = '''\
# Canonical strategies package
from .base import *          # re-export base API
from .registry import *      # re-export registry helpers
# keep subpackages import-friendly
__all__ = [name for name in globals() if not name.startswith("_")]
'''
    # Eğer boşsa/eksikse yazalım (varsa bozmayalım)
    if not target.exists() or target.read_text(encoding="utf-8").strip() == "":
        write_file(target, content, bdir)

def fix_imports(bdir: pathlib.Path):
    """Proje genelinde import yollarını strategies'e çevir."""
    changed = 0
    for py in SRC.rglob("*.py"):
        parts = set(py.parts)
        if parts & IGNORE_DIR_NAMES:
            continue
        txt = py.read_text(encoding="utf-8")
        orig = txt
        for pat, repl in PATTERNS:
            txt = pat.sub(repl, txt)
        if txt != orig:
            # backup
            bak = bdir / py.relative_to(PROJECT_ROOT)
            bak.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(py, bak)
            py.write_text(txt, encoding="utf-8")
            changed += 1
    return changed

def main():
    if not OLD.exists():
        print(f"[!] Eski yol bulunamadı: {OLD}")
        sys.exit(1)
    NEW.mkdir(parents=True, exist_ok=True)
    bdir = backup_dir()
    print(f"[i] Backup: {bdir.relative_to(PROJECT_ROOT)}")

    # 1) Tekil çekirdek dosyaları kopyala (eski -> yeni, tercih: eski/gelişkin)
    copied = []
    for fname in CORE_FILES:
        srcp = OLD / fname
        if srcp.exists():
            dstp = NEW / fname
            safe_copy(srcp, dstp, bdir)
            copied.append((srcp, dstp))
    print(f"[i] Çekirdek dosya kopyalandı: {len(copied)} adet")

    # 2) Alt dizinleri merge et (rule_based → rule)
    for old_name, new_name in DIR_MAP.items():
        moved = merge_dir(OLD / old_name, NEW / new_name, bdir)
        if moved:
            print(f"[i] {old_name} → {new_name} taşınan dosya: {len(moved)}")

    # 3) strategies/__init__.py garanti
    ensure_new_init(bdir)

    # 4) core/strategies altında shims
    make_shims(bdir)

    # 5) Projedeki importları düzelt
    changed = fix_imports(bdir)
    print(f"[i] Düzenlenen Python dosyası: {changed}")

    print("\n[✓] Entegrasyon tamam.")
    print("   - Kanonik paket: 'src/strategies'")
    print("   - Geri uyumluluk: 'src/core/strategies' shim olarak çalışıyor")
    print("   - 'algo2' importları stratejilere çevrildi (varsa).")

if __name__ == "__main__":
    main()
