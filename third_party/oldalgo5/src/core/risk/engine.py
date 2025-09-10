import numpy as np
import pandas as pd
from .config import RiskConfig

class RiskEngine:
    def __init__(self, config: RiskConfig | None = None):
        self.cfg = config or RiskConfig()

    def size_positions(self, returns: pd.Series, raw_signals: pd.Series) -> pd.Series:
        """
        Vol-target position sizing:
        w_t = clip( target_vol / realized_vol_t, 0, 1 ) * raw_signal_t

        - realized_vol: rolling std annualized
        - min_periods=1: erken barlarda 0 çıkmasın
        - 0/NaN vol -> epsilon ile değiştir
        """
        if not getattr(self.cfg, "enabled", True):
            return raw_signals.astype(float).clip(-1.0, 1.0)

        lb = int(getattr(self.cfg, "vol_lookback", 20))
        ann = float(getattr(self.cfg, "ann_factor", 252))
        target_ann_vol = float(getattr(self.cfg, "vol_target_pct", 15.0)) / 100.0

        # annualized rolling std
        realized_vol = returns.rolling(window=lb, min_periods=1).std(ddof=0) * np.sqrt(ann)

        # 0 veya NaN vol'leri güvenli hale getir
        realized_vol = realized_vol.replace(0.0, np.nan).ffill()
        if realized_vol.isna().all():
            realized_vol = pd.Series(1e-6, index=returns.index)
        else:
            first_non_nan = realized_vol.dropna().iloc[0]
            realized_vol = realized_vol.fillna(first_non_nan).replace(0.0, 1e-6)

        # ölçek = target / realized; üst sınır 1
        scale = (target_ann_vol / realized_vol).clip(upper=1.0)

        # nihai weight
        w = (raw_signals.astype(float) * scale).clip(-1.0, 1.0)
        w = w.reindex(raw_signals.index).ffill().fillna(0.0)
        return w

    def apply_stops(self, strat_returns: pd.Series, prices: pd.Series):
        """Apply basic price-based SL/TP (very simplified). Returns (adjusted_returns, logs)."""
        logs: list[str] = []
        ret = strat_returns.copy()
        if not self.cfg.enabled:
            return ret, logs

        if self.cfg.stop_loss_pct > 0:
            dd = prices / prices.cummax() - 1.0  # negative when under peak
            sl_mask = dd <= -self.cfg.stop_loss_pct / 100.0
            if sl_mask.any():
                ret.loc[sl_mask] = 0.0
                logs.append(f"Stop-Loss triggered bars: {int(sl_mask.sum())}")

        if self.cfg.take_profit_pct > 0:
            up = prices / prices.cummin() - 1.0  # positive vs min
            tp_mask = up >= self.cfg.take_profit_pct / 100.0
            if tp_mask.any():
                ret.loc[tp_mask] = 0.0
                logs.append(f"Take-Profit triggered bars: {int(tp_mask.sum())}")

        # Optional max drawdown kill-switch (very naive - whole series) 
        if self.cfg.max_dd_pct > 0:
            eq = (1 + ret.fillna(0)).cumprod()
            run_max = eq.cummax()
            dd = eq / run_max - 1.0
            if dd.min() <= -self.cfg.max_dd_pct / 100.0:
                # After crossing threshold, flatten subsequent returns
                cutoff_idx = dd.idxmin()
                ret.loc[cutoff_idx:] = 0.0
                logs.append("MaxDD threshold reached; positions flattened thereafter.")
        return ret, logs
