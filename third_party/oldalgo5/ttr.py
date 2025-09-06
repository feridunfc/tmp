# tools/replace_algo_refs.py
from __future__ import annotations
import re, sys
from pathlib import Path

EXCLUDE_DIRS = {'.git', '.venv', 'dist', 'build', '__pycache__', 'node_modules'}
INCLUDE_EXTS = {'.py', '.toml', '.yml', '.yaml'}

# regex'ler
PATTERNS = [
    # from algo2.x import ...
    (re.compile(r'(?m)^(from\s+)(?:algo2|algo3)(\.)'), r'\1src\2'),
    # import algo2.x as y, import algo3.x
    (re.compile(r'(?m)^(import\s+)(?:algo2|algo3)(\.)'), r'\1src\2'),
    # importlib.import_module("src.something")
    (re.compile(r'importlib\.import_module\(\s*[\'"](?:algo2|algo3)\.'), 'importlib.import_module("src.'),
    # düz string referansları (walk_tab içindeki candidates gibi)
    (re.compile(r'["\'](?:algo2|algo3)\.core\.backtest\.walkforward["\']'), '"src.core.backtest.walkforward"'),
    # kalan düz algo2./algo3. referansları (yorum/doküman içi HARİÇ TUTMUYOR; istersen kapat)
    #(re.compile(r'\balgo2\.'), 'src.'),
    #(re.compile(r'\balgo3\.'), 'src.'),
]

def iter_files(root: Path):
    for p in root.rglob('*'):
        if not p.is_file():
            continue
        if p.suffix.lower() not in INCLUDE_EXTS:
            continue
        parts = set(pp.lower() for pp in p.parts)
        if parts & EXCLUDE_DIRS:
            continue
        yield p

def rewrite_text(text: str) -> tuple[str, bool]:
    out = text
    changed = False
    for pat, repl in PATTERNS:
        new = pat.sub(repl, out)
        if new != out:
            changed = True
            out = new
    return out, changed

def main():
    root = Path(sys.argv[1] if len(sys.argv) > 1 else '.').resolve()
    dry = '--dry' in sys.argv
    changed_files = 0
    for f in iter_files(root):
        txt = f.read_text(encoding='utf-8', errors='ignore')
        new, ch = rewrite_text(txt)
        if ch:
            changed_files += 1
            print(f'[fix] {f}')
            if not dry:
                f.write_text(new, encoding='utf-8')
    print(f'Done. Changed files: {changed_files}')

if __name__ == '__main__':
    main()
