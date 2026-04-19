from collections import deque
from datetime import datetime
from typing import Tuple

from trading.core.config import RunConfig
from trading.core.enums import RunMode
from trading.core.events import OrderEvent, MarketEvent, SignalEvent, FillEvent
from trading.core.models import PortfolioState
from trading.execution.base import BaseExecutionAdapter
from trading.market_data.base import BaseMarketDataAdapter
from trading.metrics.engine import MetricsEngine, RunMetrics
from trading.persistence.db import get_session
from trading.persistence.repositories import FillRepository, EquitySnapshotRepository
from trading.portfolio.tracker import PortfolioTracker
from trading.risk.manager import RiskManager
from trading.strategies.base import BaseStrategy

EquitySnapshot = tuple[datetime, float, float]  # (timestamp, equity, cash)


class TradingEngine:
    def __init__(self,
               config: RunConfig,
               strategy: BaseStrategy,
               market_data: BaseMarketDataAdapter,
               execution: BaseExecutionAdapter,
               risk: RiskManager):
        self.run_config = config
        self.strategy = strategy
        self.market_data = market_data
        self.execution = execution
        self.risk = risk
        self.portfolio = PortfolioTracker(config.initial_capital)
        self.metrics = MetricsEngine(config.initial_capital, timeframe=getattr(config.market_data_config, "timeframe", "minute"))
        self.fills_buffer: list[FillEvent] = []
        self.snapshots_buffer: list[EquitySnapshot] = []

    def _persist_fill_live(self, fill: FillEvent) -> None:
        with get_session() as session:
            FillRepository(session).save_fill(self.run_config.run_id, fill)

    def _persist_snapshot_live(self, ts: datetime, equity: float, cash: float) -> None:
        with get_session() as session:
            EquitySnapshotRepository(session).save_one(self.run_config.run_id, ts, equity, cash)

    def _persist_fills_batch(self) -> None:
        if not self.fills_buffer:
            return
        with get_session() as session:
            FillRepository(session).save_fills_batch(self.run_config.run_id, self.fills_buffer)

    def run(self) -> Tuple[PortfolioState, RunMetrics, list[EquitySnapshot]]:
        queue: deque = deque()
        is_backtest = self.run_config.mode == RunMode.BACKTEST

        for market_event in self.market_data.stream():
            pending_fills = self.execution.on_market_event(market_event)  # fills prev bar's orders at today's open
            self.portfolio.mark_to_market(market_event)
            queue.extend(pending_fills)
            queue.append(market_event)

            while queue:
                event = queue.popleft()

                if isinstance(event, MarketEvent):
                    signals = self.strategy.on_market_event(event, self.portfolio.snapshot())
                    queue.extend(signals)
                elif isinstance(event, SignalEvent):
                    order_event = self.risk.evaluate(event, self.portfolio.snapshot())
                    if order_event:
                        queue.append(order_event)
                elif isinstance(event, OrderEvent):
                    fills = self.execution.submit_order(event)
                    queue.extend(fills)
                elif isinstance(event, FillEvent):
                    fill_result = self.portfolio.apply_fill(event)
                    self.metrics.on_fill(event, fill_result)
                    if is_backtest:
                        self.fills_buffer.append(event)
                    else:
                        self._persist_fill_live(event)

            state = self.portfolio.snapshot()
            self.metrics.on_bar(state.equity)
            if self.run_config.mode == RunMode.BACKTEST:
                self.snapshots_buffer.append((market_event.timestamp, state.equity, state.cash))
            else:
                self._persist_snapshot_live(market_event.timestamp, state.equity, state.cash)

        if is_backtest:
            self._persist_fills_batch()

        final_state = self.portfolio.snapshot()
        return final_state, self.metrics.summary(final_state.equity), self.snapshots_buffer

