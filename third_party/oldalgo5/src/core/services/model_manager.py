from __future__ import annotations
from typing import Dict, Optional, List
from pathlib import Path
import json
import pandas as pd
from strategies.base_ml_strategy import BaseMLStrategy
from strategies.registry import register_ml

class ModelManager:
    """Simple on-disk manager for ML strategy instances."""
    def __init__(self, models_dir: str = "models") -> None:
        self.models_dir = Path(models_dir); self.models_dir.mkdir(exist_ok=True)
        self.active: Dict[str, BaseMLStrategy] = {}

    def put(self, model_id: str, model: BaseMLStrategy) -> None:
        self.active[model_id] = model

    def train(self, model_id: str, model: BaseMLStrategy, data: pd.DataFrame, **fit_params) -> Dict:
        metrics = model.fit(data, **fit_params)
        self.save(model_id, model)
        self.active[model_id] = model
        return metrics

    def save(self, model_id: str, model: BaseMLStrategy) -> None:
        p = self.models_dir / f"{model_id}.joblib"
        model.save_model(str(p))
        meta = {
            'model_id': model_id,
            'strategy_id': model.strategy_id,
            'params': model.params,
            'metadata': model.metadata,
            'training_metrics': model.training_metrics
        }
        (self.models_dir / f"{model_id}.meta.json").write_text(json.dumps(meta, indent=2))

    def load(self, model_id: str, ctor) -> BaseMLStrategy:
        model = ctor(strategy_id=model_id)
        model.load_model(str(self.models_dir / f"{model_id}.joblib"))
        self.active[model_id] = model
        return model

    def list(self) -> List[Dict]:
        out = []
        for meta_file in self.models_dir.glob("*.meta.json"):
            try:
                out.append(json.loads(meta_file.read_text()))
            except Exception:
                out.append({'model_id': meta_file.stem.replace('.meta',''), 'status':'corrupted'})
        return out
