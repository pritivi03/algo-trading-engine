from datetime import datetime
from typing import Any
from uuid import UUID

from pydantic import BaseModel

from trading.core.config import RiskConfig, MarketDataConfig
from trading.core.enums import RunMode


class CreateRunRequest(BaseModel):
    strategy_id: UUID
    symbol: str
    mode: RunMode
    initial_capital: float
    strategy_params: dict[str, Any]
    risk_config: RiskConfig
    market_data_config: MarketDataConfig


class RunResponse(BaseModel):
    id: UUID
    strategy_id: UUID
    status: str
    container_id: str | None
    error_message: str | None
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None