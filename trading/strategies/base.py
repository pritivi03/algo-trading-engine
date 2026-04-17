from abc import ABC, abstractmethod

from trading.core.events import MarketEvent, SignalEvent
from trading.core.models import PortfolioState

class BaseStrategy(ABC):
    @abstractmethod
    def on_market_event(
            self,
            event: MarketEvent,
            portfolio: PortfolioState,
    ) -> list[SignalEvent]: ...