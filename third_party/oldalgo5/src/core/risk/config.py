class RiskConfig:
    def __init__(self, **kwargs):
        # known fields with defaults
        self.enabled = kwargs.get("enabled", True)
        self.vol_target_pct = float(kwargs.get("vol_target_pct", 15.0))   # annualized target vol (%)
        self.vol_lookback = int(kwargs.get("vol_lookback", 30))
        self.ann_factor = int(kwargs.get("ann_factor", 252))
        self.stop_loss_pct = float(kwargs.get("stop_loss_pct", 0.0))       # %
        self.take_profit_pct = float(kwargs.get("take_profit_pct", 0.0))   # %
        self.max_dd_pct = float(kwargs.get("max_dd_pct", 0.0))             # %
