from .adapters.rf import RandomForestAdapter
from .adapters.logreg import LogRegAdapter

# Optional imports
try:
    from .adapters.xgb import XGBoostAdapter  # type: ignore
except Exception:  # pragma: no cover
    XGBoostAdapter = None  # type: ignore
try:
    from .adapters.lgbm import LightGBMAdapter  # type: ignore
except Exception:  # pragma: no cover
    LightGBMAdapter = None  # type: ignore

MODEL_REGISTRY = {
    "rf": RandomForestAdapter,
    "logreg": LogRegAdapter,
}
if XGBoostAdapter is not None:
    MODEL_REGISTRY["xgb"] = XGBoostAdapter
if LightGBMAdapter is not None:
    MODEL_REGISTRY["lgbm"] = LightGBMAdapter

def list_models():
    return list(MODEL_REGISTRY.keys())

def get_model(name: str, **kwargs):
    if name not in MODEL_REGISTRY:
        raise KeyError(f"Unknown model: {name}")
    cls = MODEL_REGISTRY[name]
    return cls(**kwargs)
