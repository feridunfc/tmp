import importlib
from typing import Dict, List, Tuple
# internal fallbacks
from ui.services.strategies.ma import MA
from ui.services.strategies.rsi_meanrev import RSI_MR
from ui.services.strategies.donchian import Donchian
from ui.services.strategies.boll_meanrev import BollingerMR
from ui.services.strategies.ml_classifier import ML_Classifier

INTERNAL = [MA, RSI_MR, Donchian, BollingerMR, ML_Classifier]

def get_registry() -> Tuple[Dict[str,dict], List[Tuple[str,str]]]:
    # Try ALGO3 registry first
    try:
        m = importlib.import_module("src.core.strategies._schema")
        ext = m.get_registry()
        if ext:
            reg = {k: {"name": v["name"], "schema": v["schema"], "gen": v["gen"]} for k,v in ext.items()}
            order = [(k, v["name"]) for k,v in reg.items()]
            return reg, order
    except Exception:
        pass
    # Fallback to internal
    reg = {cls.__name__: {"name": cls.name(), "schema": cls.param_schema(), "gen": cls.generate_signals} for cls in INTERNAL}
    order = [(k, v["name"]) for k,v in reg.items()]
    return reg, order
