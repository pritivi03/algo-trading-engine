from dataclasses import dataclass, field

@dataclass
class PositionState:
    symbol: str
    qty: int
    avg_entry_price: float
    market_price: float
    unrealized_pnl: float

@dataclass
class PortfolioState:
    cash: float
    equity: float
    realized_pnl: float
    unrealized_pnl: float
    positions: dict[str, PositionState] = field(default_factory=dict)