from __future__ import annotations
import math
from dataclasses import dataclass
from typing import Any
import pandas as pd


class Rule:
    def apply(self, returns: pd.Series, weights: pd.Series):  # pure function
        raise NotImplementedError


@dataclass
class VolTargetRule(Rule):
    target_pct: float = 15.0
    lookback: int = 20
    ann: int = 252

    def apply(self, returns: pd.Series, weights: pd.Series):
        rets = returns.astype(float).fillna(0.0)
        vol = rets.ewm(span=int(max(2, self.lookback)), adjust=False).std(bias=False)
        ann_vol = vol * (float(self.ann) ** 0.5)
        scale = (float(self.target_pct) / 100.0) / ann_vol.replace(0.0, float("nan"))
        scale = scale.clip(upper=1.0).fillna(1.0)
        return (weights.astype(float) * scale).clip(0.0, 1.0)


# --- RiskChain v1 rules -------------------------------------------------


@dataclass(frozen=True)
class MaxPositionRule:
    """Maksimum pozisyon ağırlığı sınırı (clamp upper)."""

    max_w: float = 1.0

    def apply(self, returns: pd.Series, weights: pd.Series, context: dict | None = None):
        out = weights.clip(upper=float(self.max_w))
        return out.fillna(0.0)


@dataclass(frozen=True)
class CoolDownRule:
    """Kayıp/olay sonrası geçici ölçekleme.
    context: {'recent_loss': bool} veya {'cooldown_active': bool}
    """

    n_bars: int = 5  # (state taşımıyoruz; deterministik olsun)
    reduction: float = 0.5

    def apply(self, returns: pd.Series, weights: pd.Series, context: dict | None = None):
        ctx: dict[str, Any] = context or {}
        active = bool(ctx.get("recent_loss", False) or ctx.get("cooldown_active", False))
        if not active:
            return weights
        return (weights * float(self.reduction)).fillna(0.0)


@dataclass(frozen=True)
class FloorCapRule:
    """Min/Max ağırlık sınırları (clamp lower/upper)."""

    floor: float = 0.0
    cap: float = 1.0

    def apply(self, returns: pd.Series, weights: pd.Series, context: dict | None = None):
        out = weights.clip(lower=float(self.floor), upper=float(self.cap))
        return out.fillna(0.0)


@dataclass(frozen=True)
class DrawdownGuardRule:
    """Drawdown'a göre kaldıraç kırpma (opsiyonel, equity_curve verilirse işler).
    context: {'equity_curve': pd.Series}
    """

    dd_window: int = 20
    max_dd: float = 0.15  # 15% eşiğin üstündeyse ölçekle

    def apply(self, returns: pd.Series, weights: pd.Series, context: dict | None = None):
        if not isinstance(context, dict):
            return weights
        eq = context.get("equity_curve")
        if eq is None or len(eq) == 0:
            return weights

        eq = eq[-self.dd_window :]  # pencere
        roll_peak = eq.cummax()
        dd_now = float(((roll_peak - eq) / roll_peak).iloc[-1])
        if dd_now <= float(self.max_dd) or not math.isfinite(dd_now):
            return weights

        # eşiği aşınca orantısal ölçek: dd/max_dd
        scale = max(0.0, 1.0 - (dd_now / float(self.max_dd)))
        return (weights * scale).fillna(0.0)
