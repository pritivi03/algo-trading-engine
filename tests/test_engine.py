"""
End-to-end backtest integration test.

Bar sequence (short_window=3, long_window=5, qty=1):
  bars 1–5:   price=100  →  flat baseline, no signal
  bars 6–10:  price=50   →  dip, short MA stays below long MA
  bars 11–15: price=100  →  recovery; short MA crosses above long MA at bar 11 → BUY
                             short MA crosses back below at bar 15 → SELL
  bar 16:     price=200  →  SELL order from bar 15 fills at this bar's open

Expected fills:
  BUY  at bar 12 open  ≈ $100.02  (open + 2 bps slippage)
  SELL at bar 16 open  ≈ $199.96  (open - 2 bps slippage)
  Realized P&L ≈ $99.94
"""
from collections.abc import Iterator
from datetime import datetime, timezone
from uuid import uuid4

import pytest

from trading.core.config import MarketDataConfig, RiskConfig, RunConfig
from trading.core.enums import MarketDataSource, RunMode
from trading.core.events import MarketEvent
from trading.execution.simulated import SimulatedExecutionAdapter
from trading.market_data.base import BaseMarketDataAdapter
from trading.risk.manager import RiskManager
from trading.runtime.engine import TradingEngine
from trading.strategies.seeds.moving_average import MovingAverageCrossStrategy


class FixedBarsAdapter(BaseMarketDataAdapter):
    def __init__(self, symbol: str, prices: list[float], run_config: RunConfig):
        super().__init__(run_config)
        self._symbol = symbol
        self._prices = prices

    def stream(self) -> Iterator[MarketEvent]:
        for i, price in enumerate(self._prices):
            yield MarketEvent(
                symbol=self._symbol,
                timestamp=datetime(2024, 1, i + 1, tzinfo=timezone.utc),
                open=price, high=price, low=price, close=price,
                volume=10_000.0,
            )


@pytest.fixture()
def backtest_run():
    config = RunConfig(
        run_id=uuid4(),
        strategy_id=uuid4(),
        symbol="AAPL",
        mode=RunMode.BACKTEST,
        initial_capital=10_000.0,
        strategy_params={"short_window": 3, "long_window": 5},
        risk_config=RiskConfig(max_pos_size=10, max_notional_per_trade=100_000),
        market_data_config=MarketDataConfig(source=MarketDataSource.HISTORICAL, timeframe="day"),
    )
    prices = [100.0] * 5 + [50.0] * 5 + [100.0] * 5 + [200.0]
    strategy = MovingAverageCrossStrategy(short_window=3, long_window=5, qty=1)
    market_data = FixedBarsAdapter("AAPL", prices, config)
    execution = SimulatedExecutionAdapter()
    risk = RiskManager(config.risk_config)
    engine = TradingEngine(config, strategy, market_data, execution, risk)
    return engine, len(prices)


def test_backtest_produces_two_fills(test_db, backtest_run):
    engine, n_bars = backtest_run
    engine.run()

    fills = engine.fills_buffer
    assert len(fills) == 2
    assert fills[0].side == "buy"
    assert fills[1].side == "sell"


def test_backtest_fill_prices_reflect_slippage(test_db, backtest_run):
    engine, _ = backtest_run
    engine.run()

    buy_fill, sell_fill = engine.fills_buffer
    assert buy_fill.fill_price == pytest.approx(100.02, abs=0.01)
    assert sell_fill.fill_price == pytest.approx(199.96, abs=0.01)


def test_backtest_final_state_is_profitable(test_db, backtest_run):
    engine, _ = backtest_run
    final_state, metrics, snapshots = engine.run()

    assert final_state.realized_pnl == pytest.approx(99.94, abs=0.50)
    assert final_state.cash > 10_000
    assert not final_state.positions  # flat at end


def test_backtest_metrics_reflect_one_winning_trade(test_db, backtest_run):
    engine, n_bars = backtest_run
    _, metrics, snapshots = engine.run()

    assert metrics.total_trades == 1
    assert metrics.win_rate == pytest.approx(1.0)
    assert metrics.total_return_pct > 0
    assert metrics.avg_win > 0
    assert len(snapshots) == n_bars