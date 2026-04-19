import os
import uuid
from datetime import date

from dotenv import load_dotenv

from apps.runtime.factory import build_engine
from credentials.credential_store import CredentialStore
from trading.core.config import RunConfig, RiskConfig, MarketDataConfig
from trading.core.enums import RunMode, MarketDataSource
from trading.persistence.db import get_session, init_db
from trading.persistence.repositories import RunRepository, StrategyRepository, MetricsRepository

load_dotenv()


def main():
    init_db()

    strategy_id = uuid.uuid4()
    run_id = uuid.uuid4()

    config = RunConfig(
        run_id=run_id,
        strategy_id=strategy_id,
        symbol="AAPL",
        mode=RunMode.BACKTEST,
        initial_capital=100_000,
        strategy_params={"short_window": 10, "long_window": 50, "qty": 10},
        risk_config=RiskConfig(max_pos_size=100, max_notional_per_trade=50_000),
        market_data_config=MarketDataConfig(
            source=MarketDataSource.HISTORICAL,
            start_date=date(2024, 1, 1),
            end_date=date(2024, 6, 1),
        ),
    )

    creds = CredentialStore(
        ALPACA_API_KEY=os.environ["ALPACA_API_KEY"],
        ALPACA_SECRET_KEY=os.environ["ALPACA_SECRET_KEY"],
    )

    # seed strategy + run row so the FK + config_json exist
    with get_session() as session:
        StrategyRepository(session).save(strategy_id, "moving_average_cross", "# seeded")
        RunRepository(session).create(run_id, strategy_id, config)

    with get_session() as session:
        RunRepository(session).mark_started(run_id)

    try:
        engine = build_engine(creds, config)
        final_state, metrics = engine.run()

        with get_session() as session:
            MetricsRepository(session).save_metrics(run_id, metrics)
            RunRepository(session).mark_completed(run_id)
    except Exception:
        with get_session() as session:
            RunRepository(session).mark_failed(run_id)
        raise

    print(f"Run ID:              {run_id}")
    print(f"Final cash:          ${final_state.cash:,.2f}")
    print(f"Final equity:        ${final_state.equity:,.2f}")
    print(f"Realized PnL:        ${final_state.realized_pnl:,.2f}")
    print(f"Unrealized PnL:      ${final_state.unrealized_pnl:,.2f}")
    print(f"Open positions:      {list(final_state.positions.keys())}")
    print()
    print(f"Total return:        {metrics.total_return_pct:.2f}%")
    print(f"Sharpe ratio:        {metrics.sharpe_ratio:.3f}")
    print(f"Max drawdown:        {metrics.max_drawdown_pct:.2f}%")
    print(f"Win rate:            {metrics.win_rate:.1%}")
    print(f"Total trades:        {metrics.total_trades}")
    print(f"Avg win:             ${metrics.avg_win:,.2f}")
    print(f"Avg loss:            ${metrics.avg_loss:,.2f}")


if __name__ == "__main__":
    main()