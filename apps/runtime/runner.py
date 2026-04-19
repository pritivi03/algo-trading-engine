import os
import traceback
from uuid import UUID

from dotenv import load_dotenv

from apps.runtime.factory import build_engine
from credentials.credential_store import CredentialStore
from trading.persistence.db import get_session
from trading.persistence.repositories import RunRepository, MetricsRepository

load_dotenv()


def main():
    run_id = UUID(os.environ["RUN_ID"])

    creds = CredentialStore(
        ALPACA_API_KEY=os.environ["ALPACA_API_KEY"],
        ALPACA_SECRET_KEY=os.environ["ALPACA_SECRET_KEY"],
    )

    with get_session() as session:
        config = RunRepository(session).load_config(run_id)
        RunRepository(session).mark_started(run_id)

    try:
        engine = build_engine(creds, config)
        final_state, metrics = engine.run()

        with get_session() as session:
            MetricsRepository(session).save_metrics(run_id, metrics, final_state)
            RunRepository(session).mark_completed(run_id)
    except Exception:
        error_text = traceback.format_exc()
        with get_session() as session:
            RunRepository(session).mark_failed(run_id, error_message=error_text)
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