from __future__ import annotations
from typing import Dict
import pandas as pd
import asyncio

# Placeholder: provide same interface as AbstractRepository without real DB
class TimescaleRepository:
    def __init__(self, connection_string: str):
        self.cs = connection_string
    async def connect(self):
        return True
    async def save_market_data(self, symbol: str, data: pd.DataFrame):
        return True
    async def save_trade(self, trade_data: Dict):
        return True
    async def get_portfolio_history(self, days: int = 30) -> pd.DataFrame:
        return pd.DataFrame()
