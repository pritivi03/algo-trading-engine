import argparse
import uuid
from datetime import date

from dotenv import load_dotenv

from trading.core.config import RunConfig, RiskConfig, MarketDataConfig
from trading.core.enums import RunMode, MarketDataSource
from trading.persistence.db import get_session
from trading.persistence.repositories import RunRepository, StrategyRepository

load_dotenv()


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--strategy", default="moving_average", help="strategy name (matches strategies.name)")
    parser.add_argument("--symbol", default="AAPL")
    parser.add_argument("--initial-capital", type=float, default=100_000)
    parser.add_argument("--start-date", default="2024-01-01")
    parser.add_argument("--end-date", default="2024-06-01")
    args = parser.parse_args()

    run_id = uuid.uuid4()

    with get_session() as session:
        strategy_row = StrategyRepository(session).get_by_name(args.strategy)
        strategy_id = strategy_row.id
        config = RunConfig(
            run_id=run_id,
            strategy_id=strategy_id,
            symbol=args.symbol,
            mode=RunMode.BACKTEST,
            initial_capital=args.initial_capital,
            strategy_params={"short_window": 10, "long_window": 50, "qty": 10},
            risk_config=RiskConfig(max_pos_size=100, max_notional_per_trade=50_000),
            market_data_config=MarketDataConfig(
                source=MarketDataSource.HISTORICAL,
                start_date=date.fromisoformat(args.start_date),
                end_date=date.fromisoformat(args.end_date),
            ),
        )
        RunRepository(session).create(run_id, strategy_id, config)

    print(f"Run created.")
    print(f"  strategy:  {args.strategy} ({strategy_id})")
    print(f"  run_id:    {run_id}")
    print()
    print(f"Launch with: RUN_ID={run_id} uv run python -m apps.runtime.runner")


if __name__ == "__main__":
    main()
