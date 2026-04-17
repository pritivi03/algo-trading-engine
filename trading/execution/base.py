from abc import ABC, abstractmethod
from typing import Iterator

from trading.core.events import MarketEvent, SignalEvent, OrderEvent, FillEvent

class BaseExecutionAdapter(ABC):

    # Will be used to persist state from market data and order submission
    # ex: BacktestExecutionAdapter, where we will submit order can use the close price as fill price
    @abstractmethod
    def on_market_event(self, event: MarketEvent) -> None: ...

    @abstractmethod
    def submit_order(self, order: OrderEvent) -> list[FillEvent]: ...

    # for live mode, polls broker for fill events
    @abstractmethod
    def sync(self) -> list[FillEvent]: ...