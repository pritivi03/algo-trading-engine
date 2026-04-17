from abc import ABC, abstractmethod
from typing import Iterator

from trading.core.config import MarketDataConfig, RunConfig
from trading.core.events import MarketEvent

class BaseMarketDataAdapter(ABC):
    def __init__(self, run_config: RunConfig):
        self.run_config = run_config

    @abstractmethod
    def stream(self) -> Iterator[MarketEvent]: ...