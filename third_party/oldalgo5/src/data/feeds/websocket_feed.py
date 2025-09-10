from __future__ import annotations
import asyncio, json
from datetime import datetime
from typing import Dict, List, Optional
try:
    import websockets  # optional
except Exception:  # pragma: no cover
    websockets = None

import pandas as pd
from ...events.bus import EventBus
from ...events.domain import MarketDataEvent

class WebSocketDataFeed:
    def __init__(self, event_bus: EventBus, symbols: List[str], exchange: str = "binance"):
        self.event_bus = event_bus
        self.symbols = symbols
        self.exchange = exchange
        self._running = False
        self._ws = None

    async def connect(self):
        if websockets is None:
            raise RuntimeError("websockets package not installed")
        uri = self._get_uri()
        self._running = True
        try:
            async with websockets.connect(uri) as ws:
                self._ws = ws
                await self._subscribe()
                async for msg in ws:
                    self._handle_message(msg)
        except Exception as e:
            print("WebSocket error:", e)

    def _get_uri(self) -> str:
        if self.exchange == "binance":
            # simple multi-stream kline 1m uri
            streams = "/".join([f"{s.lower()}@kline_1m" for s in self.symbols])
            return f"wss://stream.binance.com:9443/stream?streams={streams}"
        return ""

    async def _subscribe(self):
        # For binance multi-stream, URL already contains subscriptions.
        pass

    def _handle_message(self, message: str):
        try:
            data = json.loads(message)
            if "stream" in data and "data" in data:
                k = data["data"].get("k", {})
                e = MarketDataEvent(
                    timestamp=datetime.utcfromtimestamp(data["data"].get("E", 0)/1000.0),
                    source=f"ws:{self.exchange}",
                    data={
                        "symbol": data["data"].get("s",""),
                        "open": float(k.get("o", 0.0)),
                        "high": float(k.get("h", 0.0)),
                        "low": float(k.get("l", 0.0)),
                        "close": float(k.get("c", 0.0)),
                        "volume": float(k.get("v", 0.0)),
                        "interval": k.get("i","1m"),
                    },
                )
                self.event_bus.publish(e)
        except Exception as ex:
            print("parse error:", ex)

# DF replay (backtest/paper) helper
async def replay_dataframe(event_bus: EventBus, df: pd.DataFrame, symbol: str, speed: float = 0.0):
    """Row-by-row market events from df with index as timestamps. speed=0 -> no sleep."""
    for ts, row in df.iterrows():
        e = MarketDataEvent(timestamp=pd.Timestamp(ts).to_pydatetime(), source="df_replay",
                            data={"symbol": symbol, "open": float(row.get("open", row.get("Open", 0.0))),
                                  "high": float(row.get("high", row.get("High", 0.0))),
                                  "low": float(row.get("low", row.get("Low", 0.0))),
                                  "close": float(row.get("close", row.get("Close", 0.0))),
                                  "volume": float(row.get("volume", row.get("Volume", 0.0)))})
        event_bus.publish(e)
        if speed > 0:
            await asyncio.sleep(speed)
