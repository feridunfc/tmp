import asyncio
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from pathlib import Path
import matplotlib.pyplot as plt
from typing import List

from src.core.event_bus import EnhancedEventBus
from src.core.events import BarClosedEvent, SignalEvent, OrderFilledEvent, PortfolioEvent, EventTopic
from src.core.payload_store import PayloadStore
from src.core.backtest_engine import EventDrivenBacktestEngine
from src.core.strategy_orchestrator import StrategyOrchestrator
from src.core.risk.engine import RiskEngine
from src.execution.backtest_gateway import BacktestExecutionGateway
from src.monitoring.event_logger import EventLogger
from src.tools.replay import EventReplayer

class TradingDemo:
    def __init__(self):
        self.event_bus = EnhancedEventBus(max_workers=15, max_queue_size=5000)
        self.payload_store = PayloadStore(Path("demo_runs/payloads"))
        self.event_logger = EventLogger(Path("demo_runs/event_logs"))
        self.risk_engine = RiskEngine(self.event_bus, {
            'position_sizing': {'base_size': 1000, 'min_position': 10},
            'constraints': {'max_position_size': 50000, 'max_leverage': 2.0}
        })
        self.strategy_orchestrator = StrategyOrchestrator(self.event_bus, self.risk_engine)
        self.execution_gateway = BacktestExecutionGateway()
        self.backtest_engine = EventDrivenBacktestEngine(self.event_bus, self.payload_store, {
            'initial_capital': 100000, 'commission': 0.001, 'slippage': 5
        })
        self.backtest_engine.attach_execution(self.execution_gateway)

        self.equity_curve = []
        self.signals = []
        self.orders = []
        self.portfolio_updates = []

        self._setup_event_handlers()

    def _setup_event_handlers(self):
        self.event_bus.subscribe(EventTopic.PORTFOLIO_UPDATE, self._on_portfolio_update)
        self.event_bus.subscribe(EventTopic.SIGNAL_GENERATED, self._on_signal)
        self.event_bus.subscribe(EventTopic.ORDER_FILLED, self._on_order_filled)
        self.event_bus.subscribe(EventTopic.BAR_CLOSED, self._log_event, is_async=True)
        self.event_bus.subscribe(EventTopic.SIGNAL_GENERATED, self._log_event, is_async=True)
        self.event_bus.subscribe(EventTopic.ORDER_FILLED, self._log_event, is_async=True)
        self.event_bus.subscribe(EventTopic.PORTFOLIO_UPDATE, self._log_event, is_async=True)

    async def _log_event(self, event):
        await self.event_logger.log_event(event)

    def _on_portfolio_update(self, event: PortfolioEvent):
        self.portfolio_updates.append({
            'timestamp': event.timestamp,
            'total_value': event.total_value,
            'cash': event.cash,
            'leverage': event.leverage
        })
        self.equity_curve.append((event.timestamp, event.total_value))

    def _on_signal(self, event: SignalEvent):
        self.signals.append({
            'timestamp': event.timestamp,
            'symbol': event.symbol,
            'direction': event.direction,
            'strength': event.strength,
            'confidence': event.confidence
        })

    def _on_order_filled(self, event: OrderFilledEvent):
        self.orders.append({
            'timestamp': event.timestamp,
            'symbol': event.symbol,
            'quantity': event.filled_quantity,
            'price': event.fill_price,
            'commission': event.commission,
            'slippage': event.slippage
        })

    def generate_sample_data(self, days: int = 30) -> pd.DataFrame:
        dates = pd.date_range(end=datetime.now(), periods=days, freq='D')
        data = []
        price = 100.0
        for date in dates:
            change = np.random.normal(0.001, 0.02)
            price *= (1 + change)
            open_price = price * (1 + np.random.normal(0, 0.005))
            high = max(open_price, price) * (1 + abs(np.random.normal(0, 0.01)))
            low = min(open_price, price) * (1 - abs(np.random.normal(0, 0.01)))
            close = price
            volume = np.random.lognormal(10, 1)
            data.append({
                'timestamp': date, 'symbol': 'AAPL',
                'open': open_price, 'high': high, 'low': low, 'close': close, 'volume': volume
            })
        return pd.DataFrame(data)

    class DemoStrategy:
        def __init__(self, strategy_id: str = "demo_momentum"):
            self.strategy_id = strategy_id
            self.previous_price = None

        async def on_bar(self, event: BarClosedEvent) -> List[SignalEvent]:
            signals = []
            if self.previous_price is not None:
                returns = (event.close - self.previous_price) / self.previous_price
                if returns > 0.01:
                    signals.append(SignalEvent(
                        strategy_id=self.strategy_id, symbol=event.symbol, direction=1,
                        strength=min(1.0, returns * 10), confidence=0.7, target_size=None
                    ))
                elif returns < -0.01:
                    signals.append(SignalEvent(
                        strategy_id=self.strategy_id, symbol=event.symbol, direction=-1,
                        strength=min(1.0, abs(returns) * 10), confidence=0.6, target_size=None
                    ))
            self.previous_price = event.close
            return signals

    async def run_demo(self):
        print("Starting Event-Driven Trading Demo")
        await self.event_bus.start()
        try:
            sample_data = self.generate_sample_data(60)
            demo_strategy = self.DemoStrategy()
            self.strategy_orchestrator.strategies["demo_momentum"] = demo_strategy
            await self.backtest_engine.run(sample_data, speed=10.0)
            await self._generate_report()
            await self._demo_replay()
        finally:
            await self.event_bus.stop()

    async def _generate_report(self):
        if not self.equity_curve:
            print("No data collected for report")
            return
        equity_df = pd.DataFrame(self.equity_curve, columns=['timestamp', 'equity']).set_index('timestamp')
        returns = equity_df['equity'].pct_change().dropna()
        total_return = (equity_df['equity'].iloc[-1] / equity_df['equity'].iloc[0] - 1) * 100
        print(f"Initial Capital: ${self.backtest_engine.initial_capital:,.2f}")
        print(f"Final Equity: ${equity_df['equity'].iloc[-1]:,.2f}")
        print(f"Total Return: {total_return:.2f}%")
        print(f"Trades: {len(self.orders)}")
        plt.figure(figsize=(10, 5))
        plt.plot(equity_df.index, equity_df['equity'], linewidth=2)
        plt.title('Equity Curve'); plt.ylabel('Equity ($)'); plt.grid(True, alpha=0.3)
        Path('demo_runs').mkdir(exist_ok=True)
        plt.savefig('demo_runs/equity_curve.png', dpi=200, bbox_inches='tight')
        print("Equity curve saved: demo_runs/equity_curve.png")

    async def _demo_replay(self):
        log_dir = Path("demo_runs/event_logs")
        if not log_dir.exists():
            print("No event logs found for replay")
            return
        files = list(log_dir.glob("*.ndjson"))
        if not files:
            print("No event logs found for replay")
            return
        latest = max(files, key=lambda p: p.stat().st_mtime)
        replay_bus = EnhancedEventBus()
        replay_bus.subscribe(EventTopic.PORTFOLIO_UPDATE, self._on_portfolio_update)
        replay_bus.subscribe(EventTopic.SIGNAL_GENERATED, self._on_signal)
        replay_bus.subscribe(EventTopic.ORDER_FILLED, self._on_order_filled)
        replayer = EventReplayer(replay_bus, self.payload_store)
        await replay_bus.start()
        try:
            await replayer.replay_events(latest, speed=20.0)
            print("Replay completed")
        finally:
            await replay_bus.stop()


async def main():
    Path("demo_runs").mkdir(exist_ok=True)
    Path("demo_runs/payloads").mkdir(exist_ok=True)
    Path("demo_runs/event_logs").mkdir(exist_ok=True)
    demo = TradingDemo()
    await demo.run_demo()

if __name__ == "__main__":
    asyncio.run(main())

