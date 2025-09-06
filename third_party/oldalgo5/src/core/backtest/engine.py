from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Any, Optional, Callable, Iterator, Tuple
from utils.data import normalize_ohlcv
import numpy as np
import pandas as pd

from utils.metrics import calculate_metrics
from core.risk.engine import RiskEngine
from strategies.registry import get_strategy  # WF'te strateji ile çalışmak için

__all__ = ["FeesConfig", "BacktestEngine", "WFSplitConfig", "WalkForwardSplitter"]


# ---------------- Walk-Forward splitter ----------------
@dataclass
class WFSplitConfig:
    n_splits: int = 3
    embargo_pct: float = 0.0
    min_train: int = 50  # ilk fold için asgari train uzunluğu


class WalkForwardSplitter:
    """
    Basit 'expanding' walk-forward:
      - Test bloğu: ardışık dilimler
      - Train: test başlangıcına kadar olan geçmiş (embargo kadar bar düşülerek)
    """
    def __init__(self, cfg: WFSplitConfig):
        assert cfg.n_splits >= 2, "n_splits >= 2 olmalı"
        assert 0.0 <= cfg.embargo_pct < 1.0, "embargo_pct [0,1) aralığında olmalı"
        self.cfg = cfg

    def split(self, df: pd.DataFrame) -> Iterator[Tuple[pd.Index, pd.Index]]:
        idx = df.index
        if not idx.is_monotonic_increasing:
            idx = idx.sort_values()
        # duplicate timestamp'leri at
        if not idx.is_unique:
            idx = idx[~idx.duplicated(keep="last")]

        n = len(idx)
        fold_len = max(1, n // self.cfg.n_splits)

        for i in range(self.cfg.n_splits):
            start = i * fold_len
            end = (i + 1) * fold_len if i < self.cfg.n_splits - 1 else n
            test_idx = idx[start:end]
            if len(test_idx) < 5:
                continue

            embargo_bars = int(len(test_idx) * self.cfg.embargo_pct)
            pre_end = max(0, start - embargo_bars)
            train_idx = idx[:pre_end]

            # İlk fold’da train çok ufaksa asgari bir boyuta yükselt
            if len(train_idx) < self.cfg.min_train:
                train_idx = idx[:max(self.cfg.min_train, fold_len)]

            yield train_idx, test_idx


# ---------------- Fees ----------------
@dataclass
class FeesConfig:
    """Basit BPS komisyon + slippage modeli."""
    commission_bps: float = 5.0
    slippage_bps: float = 10.0


# ---------------- yardımcılar ----------------
def _ensure_unique_index_df(df: pd.DataFrame) -> pd.DataFrame:
    if not df.index.is_monotonic_increasing:
        df = df.sort_index()
    if not df.index.is_unique:
        df = df[~df.index.duplicated(keep="last")]
    return df


def _ensure_unique_index_series(s: pd.Series) -> pd.Series:
    if not s.index.is_monotonic_increasing:
        s = s.sort_index()
    if not s.index.is_unique:
        s = s[~s.index.duplicated(keep="last")]
    return s


# ---------------- Backtest Engine ----------------
class BacktestEngine:
    """
    Basit bar-by-bar backtest motoru.
    - Sinyali 1 bar gecikmeli uygular (execution delay)
    - Trade değişimlerinde bps maliyeti düşer
    - RiskEngine varsa: önce vol-target sizing, sonra stop kuralları uygulanır
    - Metrikler: utils.metrics.calculate_metrics
    """

    def __init__(self, fees_config: FeesConfig = FeesConfig(), risk_engine: Optional[RiskEngine] = None):
        self.fees_config = fees_config
        self.risk_engine = risk_engine

    # ---- yardımcılar --------------------------------------------------------
    def _align_to_prices(self, df: pd.DataFrame, signals: pd.Series) -> pd.Series:
        """Sinyali df index'ine hizala, eksikleri 0 doldur; index'i normalize et."""
        df = _ensure_unique_index_df(df)
        if not isinstance(signals, pd.Series):
            raise ValueError("signals must be a pandas Series")
        signals = _ensure_unique_index_series(signals)
        sig = signals.reindex(df.index)
        return sig.fillna(0.0).astype(float)

    # ---- işlem gecikmesi ve maliyetler -------------------------------------
    def apply_delay_and_fees(self, signals: pd.Series) -> pd.Series:
        """
        1 bar gecikme + trade değişimlerinde bps maliyeti.
        Not: Maliyet sinyali küçültür; çok sık sinyal değişimi maliyeti artırır.
        """
        delayed = signals.shift(1).fillna(0.0)
        trade_changes = delayed.diff().fillna(0.0)
        bps = (self.fees_config.commission_bps + self.fees_config.slippage_bps) / 10000.0
        cost = np.abs(trade_changes) * bps
        return delayed - cost

    # ---- ana backtest -------------------------------------------------------
    def run_backtest(
        self,
        df: pd.DataFrame,
        signals: pd.Series,
        initial_capital: float = 10_000.0,
    ) -> Dict[str, Any]:
        """
        df : en az 'close' sütunu
        signals : [-1,1] yön sinyali (df ile hizalı)
        """
        df = normalize_ohlcv(df)
        if df is None or df.empty:
            raise ValueError("BacktestEngine.run_backtest: df is empty or None")
        if signals is None or len(signals) == 0:
            raise ValueError("BacktestEngine.run_backtest: signals empty or None")
        if "close" not in df.columns:
            raise ValueError("BacktestEngine.run_backtest: df must contain 'close'")

        # index normalizasyonu
        df = _ensure_unique_index_df(df)
        signals = self._align_to_prices(df, signals)

        # execution delay + costs
        net_signals = self.apply_delay_and_fees(signals)

        # piyasa getirileri
        px = df["close"].astype(float)
        rets = px.pct_change().fillna(0.0)

        # Risk: vol-target sizing (weight ∈ [0,1]) -> yön sinyali ile çarpılır
        if self.risk_engine is not None:
            weights = self.risk_engine.size_positions(rets, net_signals)
            weights = (
                _ensure_unique_index_series(weights)
                .reindex(net_signals.index)
                .ffill()
                .fillna(0.0)
                .clip(0.0, 1.0)
            )
            net_signals = net_signals * weights  # önemli!

        # strateji getirileri
        strat_returns = (net_signals * rets).astype(float)

        logs: list[str] = []
        # Stops (SL/TP/MaxDD) getiriler üzerinde çalışır
        if self.risk_engine is not None:
            strat_returns, stop_logs = self.risk_engine.apply_stops(strat_returns, px)
            if stop_logs:
                logs.extend(stop_logs)

        equity = initial_capital * (1.0 + strat_returns).cumprod()
        metrics = calculate_metrics(equity, strat_returns)

        return {
            "equity": equity,
            "returns": strat_returns,
            "metrics": metrics,
            "signals": net_signals,
            "fees_config": self.fees_config,
            "logs": logs,
        }

    # ---- walk-forward -------------------------------------------------------
    def run_walkforward(
        self,
        df: pd.DataFrame,
        strategy_name: Optional[str] = None,
        params: Optional[Dict[str, Any]] = None,
        fees: Optional[FeesConfig] = None,
        risk_engine: Optional[RiskEngine] = None,
        n_splits: int = 3,
        embargo_pct: float = 0.0,
        refit_per_fold: bool = True,  # placeholder (model tabanlı stratejiler için)
        build_signals_fn: Optional[Callable[[pd.DataFrame, pd.DataFrame], pd.Series]] = None,
        initial_capital: float = 10_000.0,
    ) -> Dict[str, Any]:
        """
        (A) strategy_name + params → train+test üzerinden sinyal üret, test dilimine kes.
        (B) build_signals_fn(train_df, test_df) → pd.Series (test ile hizalı) döndürür.
        """
        df = normalize_ohlcv(df)

        if df is None or df.empty:
            raise ValueError("run_walkforward: df empty")

        # giriş index normalizasyonu
        df = _ensure_unique_index_df(df)

        splitter = WalkForwardSplitter(WFSplitConfig(n_splits=n_splits, embargo_pct=embargo_pct))
        fees_cfg = fees or self.fees_config

        oos_equity_parts: list[pd.Series] = []
        oos_return_parts: list[pd.Series] = []
        folds_meta: list[Dict[str, Any]] = []

        for i, (train_idx, test_idx) in enumerate(splitter.split(df), start=1):
            train_df = _ensure_unique_index_df(df.loc[train_idx])
            test_df  = _ensure_unique_index_df(df.loc[test_idx])

            if build_signals_fn is not None:
                sig_test = build_signals_fn(train_df, test_df)
                if not isinstance(sig_test, pd.Series):
                    raise TypeError("build_signals_fn must return pd.Series aligned to test_df.index")
                sig_test = _ensure_unique_index_series(sig_test).reindex(test_df.index).fillna(0.0)
            else:
                if not strategy_name:
                    raise ValueError("run_walkforward: provide strategy_name or build_signals_fn")

                # expanding: train + test
                combo = _ensure_unique_index_df(pd.concat([train_df, test_df], axis=0))

                strat = get_strategy(strategy_name, **(params or {}))
                pre = strat.prepare(combo) if hasattr(strat, "prepare") else combo
                all_sig = strat.generate_signals(pre)
                all_sig = _ensure_unique_index_series(all_sig)

                # test dilimine kes
                sig_test = all_sig.reindex(test_df.index).fillna(0.0)

            # fold backtest (OOS)
            eng = BacktestEngine(
                fees_config=fees_cfg,
                risk_engine=(risk_engine or self.risk_engine),
            )
            start_cap = initial_capital if i == 1 else float(oos_equity_parts[-1].iloc[-1])
            res = eng.run_backtest(test_df, sig_test, initial_capital=start_cap)

            folds_meta.append({
                "fold": i,
                "start": test_df.index[0],
                "end": test_df.index[-1],
                "metrics": res["metrics"],
            })
            oos_equity_parts.append(res["equity"])
            oos_return_parts.append(res["returns"])

        oos_equity = pd.concat(oos_equity_parts).sort_index()
        oos_returns = pd.concat(oos_return_parts).sort_index()

        return {
            "folds": folds_meta,
            "oos_equity": oos_equity,
            "oos_returns": oos_returns,
            "config": {
                "n_splits": n_splits,
                "embargo_pct": embargo_pct,
                "refit_per_fold": refit_per_fold,
                "strategy": strategy_name,
                "params": params or {},
                "fees": vars(fees_cfg),
            },
        }
