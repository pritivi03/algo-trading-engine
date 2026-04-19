import copy
from collections import deque

from trading.core.enums import Side
from trading.core.events import FillEvent, MarketEvent
from trading.core.models import FillResult, PortfolioState, PositionState, Lot


class PortfolioTracker:
    def __init__(self, starting_capital: float):
        self.portfolio: PortfolioState = PortfolioState(
            cash=starting_capital,
            equity=starting_capital,
            realized_pnl=0,
        )

    # For now, we only allow shorts after longs (sells after buys)
    def apply_fill(self, fill: FillEvent) -> FillResult:
        symbol, fill_price, qty = fill.symbol, fill.fill_price, fill.qty
        is_buy = fill.side == Side.BUY

        if is_buy:
            self.portfolio.cash -= fill_price * qty
            lot = Lot(entry_price=fill_price, quantity=qty)
            if symbol in self.portfolio.positions:
                self.portfolio.positions[symbol].lots.append(lot)
            else:
                self.portfolio.positions[symbol] = PositionState(
                    symbol=symbol,
                    market_price=fill_price,
                    lots=deque([lot]),
                )
            self.portfolio.equity = self.portfolio.cash + self.portfolio.market_value
            return FillResult(realized_pnl=0.0)
        else:
            if symbol not in self.portfolio.positions:
                raise RuntimeError("PortfolioTracker observed short, with no existing buy positions.")

            position_state = self.portfolio.positions[symbol]
            total_held = sum(lot.quantity for lot in position_state.lots)
            if qty > total_held:
                raise ValueError(f"Cannot sell {qty} shares of {symbol}, only holding {total_held}")

            proceeds, remaining, realized = fill_price * qty, qty, 0.0
            while remaining > 0:
                if len(position_state.lots) == 0:
                    raise RuntimeError("PortfolioTracker trying to sell, but we have no existing lots")
                lot: Lot = position_state.lots.popleft()
                if lot.quantity <= remaining:
                    realized += (fill_price - lot.entry_price) * lot.quantity
                    remaining -= lot.quantity
                else:
                    realized += (fill_price - lot.entry_price) * remaining
                    lot.quantity -= remaining
                    position_state.lots.appendleft(lot)
                    remaining = 0

            self.portfolio.cash += proceeds
            self.portfolio.realized_pnl += realized
            if len(position_state.lots) == 0:
                del self.portfolio.positions[symbol]
            self.portfolio.equity = self.portfolio.cash + self.portfolio.market_value
            return FillResult(realized_pnl=realized)

    def mark_to_market(self, market_event: MarketEvent) -> None:
        symbol = market_event.symbol
        if symbol in self.portfolio.positions:
            self.portfolio.positions[symbol].market_price = market_event.close
        self.portfolio.equity = self.portfolio.cash + self.portfolio.market_value

    def snapshot(self) -> PortfolioState:
        return copy.deepcopy(self.portfolio)