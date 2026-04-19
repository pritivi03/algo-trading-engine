from datetime import datetime, timezone
from uuid import uuid4

import pytest

from trading.core.enums import Side
from trading.core.events import FillEvent, MarketEvent
from trading.portfolio.tracker import PortfolioTracker

TS = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _fill(side: Side, price: float, qty: int = 1, symbol: str = "AAPL") -> FillEvent:
    return FillEvent(symbol=symbol, timestamp=TS, order_id=uuid4(), side=side, qty=qty, fill_price=price, fees=0.0)


def _bar(price: float, symbol: str = "AAPL") -> MarketEvent:
    return MarketEvent(symbol=symbol, timestamp=TS, open=price, high=price, low=price, close=price, volume=1_000.0)


def test_buy_reduces_cash_and_opens_position():
    tracker = PortfolioTracker(starting_capital=10_000)
    tracker.apply_fill(_fill(Side.BUY, price=200, qty=3))

    state = tracker.snapshot()
    assert state.cash == pytest.approx(10_000 - 200 * 3)
    assert "AAPL" in state.positions
    assert sum(lot.quantity for lot in state.positions["AAPL"].lots) == 3


def test_sell_realizes_correct_pnl():
    tracker = PortfolioTracker(starting_capital=10_000)
    tracker.apply_fill(_fill(Side.BUY, price=100))
    result = tracker.apply_fill(_fill(Side.SELL, price=150))

    assert result.realized_pnl == pytest.approx(50.0)
    assert tracker.snapshot().realized_pnl == pytest.approx(50.0)
    assert "AAPL" not in tracker.snapshot().positions


def test_mark_to_market_updates_equity():
    tracker = PortfolioTracker(starting_capital=10_000)
    tracker.apply_fill(_fill(Side.BUY, price=100))  # cash drops to 9,900

    tracker.mark_to_market(_bar(price=150))  # position now worth 150

    # equity = cash (9,900) + market value (150) = 10,050
    assert tracker.snapshot().equity == pytest.approx(10_050)
