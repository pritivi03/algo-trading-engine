from credentials.credential_store import CredentialStore
from trading.core.config import RunConfig
from trading.core.enums import RunMode
from trading.execution.simulated import SimulatedExecutionAdapter
from trading.market_data.historical import HistoricalMarketDataAdapter
from trading.risk.manager import RiskManager
from trading.runtime.engine import TradingEngine
from trading.strategies.seeds.moving_average import MovingAverageCrossStrategy


def build_engine(credential_store: CredentialStore, config: RunConfig) -> TradingEngine:
    # TODO: resolve strategy_id from db and load dynamically
    strategy = MovingAverageCrossStrategy(
        short_window=config.strategy_params["short_window"],
        long_window=config.strategy_params["long_window"],
        qty=config.strategy_params.get("qty", 1),
    )

    risk_manager = RiskManager(config.risk_config)

    if config.mode == RunMode.BACKTEST:
        market_data = HistoricalMarketDataAdapter(credential_store, config)
        execution = SimulatedExecutionAdapter()
    elif config.mode == RunMode.LIVE:
        raise NotImplementedError("Live mode not yet supported")
    else:
        raise ValueError(f"Unknown run mode: {config.mode}")

    return TradingEngine(config, strategy, market_data, execution, risk_manager)