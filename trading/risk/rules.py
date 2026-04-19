from abc import ABC, abstractmethod

from trading.core.events import SignalEvent, OrderEvent
from trading.core.models import PortfolioState


class BaseRiskRule(ABC):
    @abstractmethod
    def validate(self, order: OrderEvent, signal: SignalEvent, portfolio: PortfolioState) -> bool:
        """Return False to reject the order."""
        ...


class MaxPositionSizeRule(BaseRiskRule):
    def __init__(self, max_qty: int):
        self.max_qty = max_qty

    def validate(self, order: OrderEvent, signal: SignalEvent, portfolio: PortfolioState) -> bool:
        position = portfolio.positions.get(order.symbol)
        current_qty = sum(lot.quantity for lot in position.lots) if position else 0
        return (current_qty + order.qty) <= self.max_qty


class MaxNotionalPerTradeRule(BaseRiskRule):
    def __init__(self, max_notional: float):
        self.max_notional = max_notional

    def validate(self, order: OrderEvent, signal: SignalEvent, portfolio: PortfolioState) -> bool:
        notional = signal.signal_price * order.qty
        return notional <= self.max_notional


class SufficientCashRule(BaseRiskRule):
    def validate(self, order: OrderEvent, signal: SignalEvent, portfolio: PortfolioState) -> bool:
        cost = signal.signal_price * order.qty
        return portfolio.cash >= cost