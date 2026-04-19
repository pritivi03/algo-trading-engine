from credentials.credential_store import CredentialStore
from trading.core.config import RunConfig
from trading.core.enums import RunMode
from trading.execution.simulated import SimulatedExecutionAdapter
from trading.execution.alpaca import AlpacaExecutionAdapter
from trading.market_data.historical import HistoricalMarketDataAdapter
from trading.market_data.live import LiveMarketDataAdapter
from trading.persistence.db import get_session
from trading.persistence.repositories import StrategyRepository
from trading.risk.manager import RiskManager
from trading.runtime.engine import TradingEngine
from trading.strategies.base import BaseStrategy
from trading.strategies.loader import load_strategy_from_code


def _load_strategy(config: RunConfig) -> BaseStrategy:
    with get_session() as session:
        row = StrategyRepository(session).get(config.strategy_id)
        code = row.code
    return load_strategy_from_code(code, config.strategy_params)


def build_engine(credential_store: CredentialStore, config: RunConfig) -> TradingEngine:
    strategy = _load_strategy(config)
    risk_manager = RiskManager(config.risk_config)

    if config.mode == RunMode.BACKTEST:
        market_data = HistoricalMarketDataAdapter(credential_store, config)
        execution = SimulatedExecutionAdapter()
    elif config.mode in (RunMode.PAPER, RunMode.LIVE):
        market_data = LiveMarketDataAdapter(credential_store, config)
        execution = AlpacaExecutionAdapter(
            api_key=credential_store.ALPACA_API_KEY,
            secret_key=credential_store.ALPACA_SECRET_KEY,
            paper=(config.mode == RunMode.PAPER),
        )
    else:
        raise ValueError(f"Unknown run mode: {config.mode}")

    return TradingEngine(config, strategy, market_data, execution, risk_manager)