from trading.core.enums import Side
from trading.core.events import MarketEvent, SignalEvent
from trading.core.models import PortfolioState
from trading.strategies.base import BaseStrategy


class RSIStrategy(BaseStrategy):
    """
    Aggressive mean-reversion strategy using RSI.
    Buys on oversold conditions, sells on overbought.
    Uses a larger default qty for more aggressive exposure.
    """

    def __init__(self, rsi_period: int = 7, oversold: float = 35, overbought: float = 65, qty: int = 5):
        self.rsi_period = rsi_period
        self.oversold = oversold
        self.overbought = overbought
        self.qty = qty
        self._closes: list[float] = []

    def _rsi(self) -> float | None:
        if len(self._closes) < self.rsi_period + 1:
            return None
        deltas = [self._closes[i] - self._closes[i - 1] for i in range(-self.rsi_period, 0)]
        gains = sum(d for d in deltas if d > 0)
        losses = sum(-d for d in deltas if d < 0)
        avg_gain = gains / self.rsi_period
        avg_loss = losses / self.rsi_period
        if avg_loss == 0:
            return 100.0
        rs = avg_gain / avg_loss
        return 100.0 - (100.0 / (1.0 + rs))

    def on_market_event(self, event: MarketEvent, portfolio: PortfolioState) -> list[SignalEvent]:
        self._closes.append(event.close)

        rsi = self._rsi()
        if rsi is None:
            return []

        position = portfolio.positions.get(event.symbol)
        held_qty = sum(lot.quantity for lot in position.lots) if position else 0

        if rsi < self.oversold and held_qty == 0:
            return [SignalEvent(
                symbol=event.symbol,
                timestamp=event.timestamp,
                side=Side.BUY,
                signal_price=event.close,
                qty=self.qty,
            )]

        if rsi > self.overbought and held_qty > 0:
            return [SignalEvent(
                symbol=event.symbol,
                timestamp=event.timestamp,
                side=Side.SELL,
                signal_price=event.close,
                qty=held_qty,
            )]

        return []
