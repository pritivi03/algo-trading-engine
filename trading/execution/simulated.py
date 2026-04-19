from trading.core.enums import Side
from trading.core.events import FillEvent, OrderEvent, MarketEvent
from trading.execution.base import BaseExecutionAdapter

SLIPPAGE_BPS = 2.0   # 2 basis points per side
FEE_RATE = 0.0005    # 0.05% of notional per fill


class SimulatedExecutionAdapter(BaseExecutionAdapter):
    def __init__(self):
        self._pending_orders: list[OrderEvent] = []

    def on_market_event(self, event: MarketEvent) -> list[FillEvent]:
        if not self._pending_orders:
            return []

        fills = []
        for order in self._pending_orders:
            slippage = event.open * (SLIPPAGE_BPS / 10_000)
            if order.side == Side.BUY:
                fill_price = event.open + slippage
            else:
                fill_price = event.open - slippage

            fills.append(FillEvent(
                order_id=order.order_id,
                timestamp=event.timestamp,
                symbol=event.symbol,
                side=order.side,
                fill_price=fill_price,
                qty=order.qty,
                fees=round(fill_price * order.qty * FEE_RATE, 4),
            ))

        self._pending_orders = []
        return fills

    def submit_order(self, order: OrderEvent) -> list[FillEvent]:
        self._pending_orders.append(order)
        return []

    def sync(self) -> list[FillEvent]:
        return []
