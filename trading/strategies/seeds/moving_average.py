from collections import deque

from trading.core.enums import Side
from trading.core.events import MarketEvent, SignalEvent
from trading.core.models import PortfolioState
from trading.strategies.base import BaseStrategy


class MovingAverageCrossStrategy(BaseStrategy):
    def __init__(self, short_window: int, long_window: int, qty: int = 1):
        self.short_window = short_window
        self.long_window = long_window
        self.qty = qty
        self.prices: deque[float] = deque(maxlen=long_window)
        self._prev_short_ma: float | None = None
        self._prev_long_ma: float | None = None

    def on_market_event(self, event: MarketEvent, portfolio: PortfolioState) -> list[SignalEvent]:
        self.prices.append(event.close)

        if len(self.prices) < self.long_window:
            return []

        short_ma = sum(list(self.prices)[-self.short_window:]) / self.short_window
        long_ma = sum(self.prices) / self.long_window

        signals = []
        if self._prev_short_ma is not None and self._prev_long_ma is not None:
            prev_above = self._prev_short_ma > self._prev_long_ma
            curr_above = short_ma > long_ma

            if not prev_above and curr_above:
                # short MA crossed above long MA — buy signal
                signals.append(SignalEvent(
                    symbol=event.symbol,
                    timestamp=event.timestamp,
                    side=Side.BUY,
                    signal_price=event.close,
                    qty=self.qty,
                ))
            elif prev_above and not curr_above and event.symbol in portfolio.positions:
                # short MA crossed below long MA and we hold a position — sell signal
                total_qty = sum(lot.quantity for lot in portfolio.positions[event.symbol].lots)
                signals.append(SignalEvent(
                    symbol=event.symbol,
                    timestamp=event.timestamp,
                    side=Side.SELL,
                    signal_price=event.close,
                    qty=total_qty,
                ))

        self._prev_short_ma = short_ma
        self._prev_long_ma = long_ma
        return signals