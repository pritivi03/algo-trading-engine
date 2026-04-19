import os
import uuid
from datetime import date

from dotenv import load_dotenv

from apps.runtime.factory import build_engine
from credentials.credential_store import CredentialStore
from trading.core.config import RunConfig, RiskConfig, MarketDataConfig
from trading.core.enums import RunMode, MarketDataSource

load_dotenv()

def main():
    config = RunConfig(
        run_id=uuid.uuid4(),
        strategy_id=uuid.uuid4(),
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

    engine = build_engine(creds, config)
    final_state, metrics = engine.run()

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