from dataclasses import dataclass, field

'''
To calculate unrealized pnl, we will be using avg_entry_price instead of maintaining list[Lot].
Where one Lot = (entry_price, quantity)
'''
@dataclass
class PositionState:
    symbol: str
    qty: int # positive = long, negative = short
    avg_entry_price: float # new_avg = (existing_qty * avg_entry_price + new_qty * fill_price) / (existing_qty + new_qty)
    market_price: float # latest bar close
    unrealized_pnl: float

@dataclass
class PortfolioState:
    cash: float
    equity: float # what would be worth, if liquidated all -> cash + sum(unrealized pnl of all positions)
    realized_pnl: float
    unrealized_pnl: float
    positions: dict[str, PositionState] = field(default_factory=dict)