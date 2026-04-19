from datetime import datetime, timezone

from trading.core.config import RiskConfig
from trading.core.enums import Side
from trading.core.events import SignalEvent
from trading.core.models import PortfolioState
from trading.risk.manager import RiskManager

TS = datetime(2024, 1, 1, tzinfo=timezone.utc)


def _signal(price: float = 100.0, qty: int = 1, side: Side = Side.BUY) -> SignalEvent:
    return SignalEvent(symbol="AAPL", timestamp=TS, side=side, signal_price=price, qty=qty)


def _portfolio(cash: float = 10_000.0) -> PortfolioState:
    return PortfolioState(cash=cash, equity=cash, realized_pnl=0.0)


def _risk(**kwargs) -> RiskManager:
    defaults = {"max_pos_size": 100, "max_notional_per_trade": 1_000_000}
    defaults.update(kwargs)
    return RiskManager(RiskConfig(**defaults))


def test_max_position_size_blocks_oversized_buy():
    risk = _risk(max_pos_size=5)
    assert risk.evaluate(_signal(qty=6), _portfolio()) is None


def test_max_notional_blocks_expensive_trade():
    risk = _risk(max_notional_per_trade=500)
    # 6 shares @ $100 = $600 notional > $500 limit
    assert risk.evaluate(_signal(price=100.0, qty=6), _portfolio()) is None


def test_insufficient_cash_blocks_buy():
    risk = _risk()
    # 50 shares @ $100 = $5,000 cost; portfolio only has $1,000 cash
    assert risk.evaluate(_signal(price=100.0, qty=50), _portfolio(cash=1_000)) is None


def test_valid_order_passes_all_rules():
    risk = _risk(max_pos_size=10, max_notional_per_trade=5_000)
    order = risk.evaluate(_signal(price=100.0, qty=10), _portfolio())
    assert order is not None
    assert order.qty == 10
    assert order.side == Side.BUY