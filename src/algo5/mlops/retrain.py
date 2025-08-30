
from __future__ import annotations

def should_retrain(psi_scores: dict[str, float], threshold: float = 0.2, min_features: int = 2) -> bool:
    """Return True if enough features exceed PSI threshold."""
    trig = [k for k, v in psi_scores.items() if v >= threshold]
    return len(trig) >= min_features
