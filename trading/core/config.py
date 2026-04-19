from datetime import date
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from trading.core.enums import MarketDataSource, RunMode

class RiskConfig(BaseModel):
    max_pos_size: int
    max_notional_per_trade: float
    stop_loss_pct: float | None = None
    take_profit_pct: float | None = None
    cooldown_bars: int = 0

class MarketDataConfig(BaseModel):
    source: MarketDataSource
    start_date: date | None = None
    end_date: date | None = None
    timeframe: str = "minute"  # minute | hour | day

class RunConfig(BaseModel):
    run_id: UUID
    strategy_id: UUID
    symbol: str
    mode: RunMode
    initial_capital: float
    strategy_params: dict[str, Any]
    risk_config: RiskConfig
    market_data_config: MarketDataConfig
