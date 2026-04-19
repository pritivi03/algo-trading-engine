from trading.core.events import FillEvent, OrderEvent, MarketEvent
from trading.execution.base import BaseExecutionAdapter


class SimulatedExecutionAdapter(BaseExecutionAdapter):
    def __init__(self):
        self.last_event: MarketEvent | None = None

    def on_market_event(self, event: MarketEvent) -> None:
        self.last_event = event

    def submit_order(self, order: OrderEvent) -> list[FillEvent]:
        if self.last_event is None:
            raise RuntimeError("SimulatedExecutionAdapter - no market event to simulate fill")

        simulated_fill_event = FillEvent(
            order_id=order.order_id,
            timestamp=self.last_event.timestamp,
            symbol=self.last_event.symbol,
            side=order.side,
            fill_price=self.last_event.close,
            qty=order.qty,
            fees=0
        )

        return [simulated_fill_event]

    # Only used for live mode
    def sync(self) -> list[FillEvent]:
        return []