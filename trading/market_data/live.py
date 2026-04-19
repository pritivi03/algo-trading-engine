import queue
import threading
from collections.abc import Iterator

from alpaca.data.live import CryptoDataStream, StockDataStream
from alpaca.data.models import Bar

from credentials.credential_store import CredentialStore
from trading.core.config import RunConfig
from trading.core.enums import RunMode
from trading.core.events import MarketEvent
from trading.market_data.base import BaseMarketDataAdapter
from trading.market_data.historical import is_crypto


class LiveMarketDataAdapter(BaseMarketDataAdapter):
    def __init__(self, credential_store: CredentialStore, run_config: RunConfig):
        super().__init__(run_config)
        if run_config.mode not in (RunMode.PAPER, RunMode.LIVE):
            raise RuntimeError("LiveMarketDataAdapter is only for PAPER/LIVE mode")
        self._creds = credential_store
        self._stop_event: threading.Event | None = None

    def signal_stop(self) -> None:
        if self._stop_event:
            self._stop_event.set()

    def stream(self) -> Iterator[MarketEvent]:
        symbol = self.run_config.symbol
        bar_queue: queue.Queue = queue.Queue(maxsize=256)
        stop_event = threading.Event()
        self._stop_event = stop_event

        if is_crypto(symbol):
            wss = CryptoDataStream(
                api_key=self._creds.ALPACA_API_KEY,
                secret_key=self._creds.ALPACA_SECRET_KEY,
            )
        else:
            wss = StockDataStream(
                api_key=self._creds.ALPACA_API_KEY,
                secret_key=self._creds.ALPACA_SECRET_KEY,
            )

        async def on_bar(bar: Bar) -> None:
            bar_queue.put_nowait(bar)

        wss.subscribe_bars(on_bar, symbol)
        thread = threading.Thread(target=wss.run, daemon=True)
        thread.start()

        while not stop_event.is_set():
            try:
                bar = bar_queue.get(timeout=1.0)
            except queue.Empty:
                continue
            yield MarketEvent(
                symbol=symbol,
                timestamp=bar.timestamp,
                open=float(bar.open),
                high=float(bar.high),
                low=float(bar.low),
                close=float(bar.close),
                volume=float(bar.volume),
            )
        # daemon thread dies on process exit — no explicit cleanup needed