from collections.abc import Iterator
from datetime import datetime

from alpaca.data import StockBarsRequest, BarSet, Bar
from alpaca.data.historical.crypto import CryptoHistoricalDataClient
from alpaca.data.historical.stock import StockHistoricalDataClient
from alpaca.data.requests import CryptoBarsRequest
from alpaca.data.timeframe import TimeFrame, TimeFrameUnit

from credentials.credential_store import CredentialStore
from trading.core.config import RunConfig
from trading.core.enums import RunMode
from trading.core.events import MarketEvent
from trading.market_data.base import BaseMarketDataAdapter

_TIMEFRAME_MAP = {
    "minute": TimeFrame(1, TimeFrameUnit.Minute),
    "hour": TimeFrame(1, TimeFrameUnit.Hour),
    "day": TimeFrame(1, TimeFrameUnit.Day),
}


def is_crypto(symbol: str) -> bool:
    return "/" in symbol


class HistoricalMarketDataIterator(Iterator[MarketEvent]):
    def __init__(self, symbol: str, bars: list[Bar]):
        self.symbol = symbol
        self.index = 0
        self.bars = bars

    def __iter__(self) -> "HistoricalMarketDataIterator":
        return self

    def __next__(self) -> MarketEvent:
        if self.index >= len(self.bars):
            raise StopIteration
        bar = self.bars[self.index]
        self.index += 1
        return MarketEvent(
            symbol=self.symbol,
            timestamp=bar.timestamp,
            open=bar.open,
            high=bar.high,
            low=bar.low,
            close=bar.close,
            volume=bar.volume,
        )


class HistoricalMarketDataAdapter(BaseMarketDataAdapter):
    def __init__(self, credential_store: CredentialStore, run_config: RunConfig):
        super().__init__(run_config)
        if run_config.mode != RunMode.BACKTEST:
            raise RuntimeError("HistoricalMarketDataAdapter invoked with RunConfig not for Backtest")
        self._credential_store = credential_store

    def stream(self) -> Iterator[MarketEvent]:
        symbol = self.run_config.symbol
        market_data_config = self.run_config.market_data_config

        if market_data_config.start_date is None:
            raise RuntimeError("HistoricalMarketDataAdapter missing start_date in MarketDataConfig")
        if market_data_config.end_date is None:
            raise RuntimeError("HistoricalMarketDataAdapter missing end_date in MarketDataConfig")

        tf = _TIMEFRAME_MAP.get(market_data_config.timeframe or "minute", TimeFrame(1, TimeFrameUnit.Minute))
        start = datetime.combine(market_data_config.start_date, datetime.min.time())
        end = datetime.combine(market_data_config.end_date, datetime.max.time())

        if is_crypto(symbol):
            client = CryptoHistoricalDataClient(
                self._credential_store.ALPACA_API_KEY,
                self._credential_store.ALPACA_SECRET_KEY,
            )
            req = CryptoBarsRequest(symbol_or_symbols=symbol, start=start, end=end, timeframe=tf)
            bar_set = client.get_crypto_bars(req)
        else:
            client = StockHistoricalDataClient(
                self._credential_store.ALPACA_API_KEY,
                self._credential_store.ALPACA_SECRET_KEY,
            )
            req = StockBarsRequest(symbol_or_symbols=symbol, start=start, end=end, timeframe=tf)
            bar_set = client.get_stock_bars(req)

        if not isinstance(bar_set, BarSet):
            raise RuntimeError("Expected BarSet from data client")

        bars = bar_set.data[symbol]
        return HistoricalMarketDataIterator(symbol, bars)

