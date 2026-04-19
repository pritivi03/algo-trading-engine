from datetime import datetime
from uuid import UUID, uuid4

from pydantic import BaseModel, Field

from trading.core.enums import Side, OrderType, OrderStatus

class BaseEvent(BaseModel):
    symbol: str
    timestamp: datetime

class MarketEvent(BaseEvent):
    open: float
    high: float
    low: float
    close: float
    volume: float

class SignalEvent(BaseEvent):
    side: Side
    signal_price: float
    qty: int = 1

class OrderEvent(BaseEvent):
    order_id: UUID = Field(default_factory=uuid4)
    side: Side
    qty: int
    order_type: OrderType
    limit_price: float | None = None
    order_status: OrderStatus = OrderStatus.OPEN

class FillEvent(BaseEvent):
    fill_id: UUID = Field(default_factory=uuid4)
    order_id: UUID
    side: Side
    qty: int
    fill_price: float
    fees: float
