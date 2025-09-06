import pandas as pd

class PaperBroker:
    def __init__(self, cash=100000.0):
        self.cash = float(cash)
        self.pos = 0
        self.entry_price = None
        self.trades = []
        self.equity_curve = []

    def step(self, time, price, target_pos):
        if target_pos != self.pos:
            if self.pos == 1:
                pnl = (price - self.entry_price)
                self.cash += pnl
                self.trades.append({"time": time, "side": "SELL", "price": float(price), "pnl": float(pnl)})
            if target_pos == 1:
                self.entry_price = price
                self.trades.append({"time": time, "side": "BUY", "price": float(price), "pnl": 0.0})
            else:
                self.entry_price = None
            self.pos = target_pos
        eq = self.cash + (price - (self.entry_price if self.entry_price is not None else price)) * (1 if self.pos==1 else 0)
        self.equity_curve.append({"time": time, "equity": float(eq)})

    def results(self):
        df_trades = pd.DataFrame(self.trades)
        df_eq = pd.DataFrame(self.equity_curve).set_index("time")
        return df_trades, df_eq
