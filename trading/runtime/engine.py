from collections import deque
from typing import Tuple

from trading.core.config import RunConfig
from trading.core.events import OrderEvent, MarketEvent, SignalEvent, FillEvent
from trading.core.models import PortfolioState
from trading.execution.base import BaseExecutionAdapter
from trading.market_data.base import BaseMarketDataAdapter
from trading.metrics.engine import MetricsEngine, RunMetrics
from trading.portfolio.tracker import PortfolioTracker
from trading.risk.manager import RiskManager
from trading.strategies.base import BaseStrategy

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
        self.metrics = MetricsEngine(config.initial_capital)

    def run(self) -> Tuple[PortfolioState, RunMetrics]:
        queue: deque = deque()

        for market_event in self.market_data.stream():
            self.portfolio.mark_to_market(market_event)
            self.execution.on_market_event(market_event)
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

            self.metrics.on_bar(self.portfolio.portfolio.equity)

        final_state = self.portfolio.snapshot()
        return final_state, self.metrics.summary(final_state.equity)

