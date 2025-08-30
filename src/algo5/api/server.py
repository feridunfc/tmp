from __future__ import annotations
from dataclasses import dataclass, field
from typing import Dict, Any
from .security import require_api_key
@dataclass
class APIServer:
    api_key: str = ""; _runs: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    def strategies_list(self, key: str | None = None) -> Dict[str, Any]:
        require_api_key(self.api_key, key); return {"strategies": ["sma_crossover","rsi_threshold","macd_signal"]}
    def backtest_run(self, config: Dict[str, Any], key: str | None = None) -> Dict[str, Any]:
        require_api_key(self.api_key, key); rid = f"run_{len(self._runs)+1:04d}"; self._runs[rid] = {"config":config,"status":"ok"}; return {"run_id": rid, "status":"ok"}
    def runs(self, key: str | None = None) -> Dict[str, Any]:
        require_api_key(self.api_key, key); return {"runs": list(self._runs.keys())}
