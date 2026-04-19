from dataclasses import dataclass, field
from collections import deque

'''
To calculate unrealized pnl, we will be using avg_entry_price instead of maintaining list[Lot].
Where one Lot = (entry_price, quantity)

For quantity, positive is long, negative is short.
'''
@dataclass
class FillResult:
    realized_pnl: float  # 0.0 for buys, actual gain/loss for sells

@dataclass
class Lot:
    entry_price: float
    quantity: int

@dataclass
class PositionState:
    symbol: str
    market_price: float
    lots: deque[Lot] = field(default_factory=deque)

    @property
    def unrealized_pnl(self) -> float:
        # go through all lots
        return sum((self.market_price - lot.entry_price) * lot.quantity for lot in self.lots)

@dataclass
class PortfolioState:
    cash: float
    equity: float # what would be worth, if liquidated all -> cash + sum(unrealized pnl of all positions)
    realized_pnl: float
    positions: dict[str, PositionState] = field(default_factory=dict)

    @property
    def unrealized_pnl(self) -> float:
        return sum(p.unrealized_pnl for p in self.positions.values())

    @property
    def market_value(self) -> float:
        return sum(
            p.market_price * sum(l.quantity for l in p.lots)
            for p in self.positions.values()
        )
