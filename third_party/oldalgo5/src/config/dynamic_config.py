from __future__ import annotations
from typing import Dict, Any, Optional
from pathlib import Path
import yaml, json

class DynamicConfigManager:
    def __init__(self, config_path: str = "config"):
        self.base = Path(config_path)
        self._cache: Dict[str, Any] = {}
        self.reload_all()

    def reload_all(self):
        self._cache.clear()
        if self.base.exists():
            for p in self.base.glob("*.yaml"):
                with open(p, "r", encoding="utf-8") as f:
                    self._cache[p.stem] = yaml.safe_load(f) or {}

    def get(self, name: str) -> Dict[str, Any]:
        return dict(self._cache.get(name, {}))

    def get_strategy_params(self, strategy_name: str) -> Dict[str, Any]:
        s = self._cache.get("strategies", {}).get("strategies", {})
        return dict(s.get(strategy_name, {}).get("parameters", {}))

    def get_risk_params(self) -> Dict[str, Any]:
        return dict(self._cache.get("risk", {}).get("risk", {}))

    def update(self, name: str, cfg: Dict[str, Any]) -> None:
        self._cache[name] = cfg
        path = self.base / f"{name}.yaml"
        with open(path, "w", encoding="utf-8") as f:
            yaml.safe_dump(cfg, f, allow_unicode=True)
