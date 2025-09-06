"""
Optional auto register hook.

If you maintain a manifest of modules that perform @register_strategy at import time,
list them in MANIFEST. This avoids importing the whole strategies package on bootstrap.
"""
from importlib import import_module

# Fill with your light modules that only register via decorators.
MANIFEST = [
    # "strategies.rule_based.atr_breakout",
    # "strategies.ai.random_forest",
]

def bootstrap() -> int:
    added = 0
    for m in MANIFEST:
        try:
            import_module(m)
            added += 1
        except Exception:
            pass
    return added
