import time
from datetime import datetime, timezone

from alpaca.trading.client import TradingClient
from alpaca.trading.enums import OrderSide, TimeInForce
from alpaca.trading.enums import OrderStatus as AlpacaOrderStatus
from alpaca.trading.requests import MarketOrderRequest

from trading.core.enums import Side
from trading.core.events import FillEvent, MarketEvent, OrderEvent
from trading.execution.base import BaseExecutionAdapter


class AlpacaExecutionAdapter(BaseExecutionAdapter):
    def __init__(self, api_key: str, secret_key: str, paper: bool = True):
        self._client = TradingClient(api_key, secret_key, paper=paper)

    def on_market_event(self, event: MarketEvent) -> list[FillEvent]:
        return []  # fills come back synchronously from submit_order

    def submit_order(self, order: OrderEvent) -> list[FillEvent]:
        # crypto markets are 24/7 — GTC; equities use DAY
        tif = TimeInForce.GTC if "/" in order.symbol else TimeInForce.DAY
        req = MarketOrderRequest(
            symbol=order.symbol,
            qty=order.qty,
            side=OrderSide.BUY if order.side == Side.BUY else OrderSide.SELL,
            time_in_force=tif,
        )
        result = self._client.submit_order(order_data=req)
        filled = self._wait_for_fill(str(result.id))
        if not filled:
            return []
        return [FillEvent(
            symbol=order.symbol,
            timestamp=filled.filled_at or datetime.now(timezone.utc),
            order_id=order.order_id,
            side=order.side,
            qty=int(float(filled.filled_qty)),
            fill_price=float(filled.filled_avg_price),
            fees=0.0,  # Alpaca charges no commissions
        )]

    def sync(self) -> list[FillEvent]:
        return []

    def _wait_for_fill(self, order_id: str, timeout: float = 15.0):
        deadline = time.time() + timeout
        while time.time() < deadline:
            o = self._client.get_order_by_id(order_id)
            if o.status in (AlpacaOrderStatus.FILLED, AlpacaOrderStatus.PARTIALLY_FILLED):
                return o
            time.sleep(0.5)
        return None
