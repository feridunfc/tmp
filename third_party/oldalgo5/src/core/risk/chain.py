from __future__ import annotations
from typing import List, Tuple
from .rules import BaseRule, RiskContext

class RiskChain:
    def __init__(self, rules: List[BaseRule]):
        self.rules = rules

    def validate(self, symbol: str, proposed_weight: float, ctx: RiskContext) -> Tuple[bool, float, List[str]]:
        msgs = []
        ok_all = True
        w = proposed_weight
        for rule in self.rules:
            ok, w, reason = rule.validate(symbol, w, ctx)
            msgs.append(f"{rule.name}: {reason}")
            ok_all = ok_all and ok
        return ok_all, w, msgs
