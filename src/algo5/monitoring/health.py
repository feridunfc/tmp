from __future__ import annotations
from typing import Callable, Dict, List, Tuple
class HealthChecker:
    def __init__(self): self._checks: List[Tuple[str, Callable[[], bool]]] = []
    def add_check(self, name: str, fn: Callable[[], bool]) -> None: self._checks.append((name, fn))
    def run(self) -> Dict[str, bool]:
        out: Dict[str, bool] = {}
        for name, fn in self._checks:
            try: out[name] = bool(fn())
            except Exception: out[name] = False
        return out
