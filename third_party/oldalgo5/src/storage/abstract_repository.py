from __future__ import annotations
from abc import ABC, abstractmethod
from typing import Dict
import pandas as pd

class AbstractRepository(ABC):
    @abstractmethod
    async def connect(self): ...
    @abstractmethod
    async def save_market_data(self, symbol: str, data: pd.DataFrame): ...
    @abstractmethod
    async def save_trade(self, trade_data: Dict): ...
    @abstractmethod
    async def get_portfolio_history(self, days: int = 30) -> pd.DataFrame: ...
