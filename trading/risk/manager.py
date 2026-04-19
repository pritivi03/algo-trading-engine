from trading.core.config import RiskConfig
from trading.core.enums import OrderType
from trading.core.events import SignalEvent, OrderEvent
from trading.core.models import PortfolioState
from trading.risk.rules import BaseRiskRule, MaxPositionSizeRule, MaxNotionalPerTradeRule, SufficientCashRule


class RiskManager:
    def __init__(self, config: RiskConfig):
        self.rules: list[BaseRiskRule] = [
            MaxPositionSizeRule(config.max_pos_size),
            MaxNotionalPerTradeRule(config.max_notional_per_trade),
            SufficientCashRule(),
        ]

    def evaluate(self, signal: SignalEvent, portfolio: PortfolioState) -> OrderEvent | None:
        order = OrderEvent(
            symbol=signal.symbol,
            timestamp=signal.timestamp,
            side=signal.side,
            qty=signal.qty,
            order_type=OrderType.MARKET,
        )

        for rule in self.rules:
            if not rule.validate(order, signal, portfolio):
                return None

        return order