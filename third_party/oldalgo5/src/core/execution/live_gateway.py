
from __future__ import annotations
from .gateway import ExecutionGateway, OrderEvent, FillEvent

class BinanceGateway(ExecutionGateway):
    """REST/WebSocket entegrasyonuna hazır iskelet. Güvenli varsayılan: NotImplemented."""
    def __init__(self, api_key: str = '', api_secret: str = '', testnet: bool = True):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.testnet = testnet

    def place_order(self, order: OrderEvent, market_price: float) -> FillEvent:
        raise NotImplementedError("Integrate with Binance REST (testnet) here.")

class AlpacaGateway(ExecutionGateway):
    def __init__(self, api_key: str = '', api_secret: str = '', paper: bool = True):
        super().__init__()
        self.api_key = api_key
        self.api_secret = api_secret
        self.paper = paper

    def place_order(self, order: OrderEvent, market_price: float) -> FillEvent:
        raise NotImplementedError("Integrate with Alpaca REST here.")
