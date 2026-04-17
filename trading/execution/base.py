from abc import ABC, abstractmethod
from typing import Iterator

from trading.core.events import MarketEvent, SignalEvent, OrderEvent, FillEvent

class BaseExecutionAdapter(ABC):
    @abstractmethod
    def on_market_event(self, event: MarketEvent) -> None: ...

    @abstractmethod
    def submit_order(self, order: OrderEvent) -> list[FillEvent]: ...

    # for paper mode, polls broker for fill events
    @abstractmethod
    def sync(self) -> list[FillEvent]: ...