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
    config: dict[str, Any]
    created_at: datetime
    started_at: datetime | None
    completed_at: datetime | None


class MetricsResponse(BaseModel):
    run_id: UUID
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    avg_win: float
    avg_loss: float
    final_cash: float
    final_equity: float
    realized_pnl: float
    unrealized_pnl: float
    updated_at: datetime


class FillResponse(BaseModel):
    id: UUID
    order_id: UUID
    symbol: str
    side: str
    qty: int
    fill_price: float
    fees: float
    timestamp: datetime