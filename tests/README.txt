
Fix: ScopeMismatch with pytest monkeypatch

- Changes `_cache_root` fixture to FUNCTION scope (was session), so it can use `monkeypatch`.
- Adds deterministic seed fixture (auto-used).
- Adds optional import-path shim for local runs without `pip install -e .`.

Usage:
1) Replace your existing `tests/conftest.py` with this one.
2) Run: `pytest tests/data -q`
