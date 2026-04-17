import uuid
from datetime import datetime

import uvicorn
from fastapi import FastAPI
from dotenv import load_dotenv
import os

from credentials.credential_store import CredentialStore
from trading.core.config import RunConfig, RiskConfig, MarketDataConfig
from trading.core.enums import RunMode, MarketDataSource
from trading.market_data.historical import HistoricalMarketDataAdapter

load_dotenv()

app = FastAPI(title="Algo Trading Engine")

@app.get("/health")
async def health():
    credential_store = CredentialStore(ALPACA_API_KEY=os.environ["ALPACA_API_KEY"], ALPACA_SECRET_KEY=os.environ["ALPACA_SECRET_KEY"])

    run_config = RunConfig(
        run_id=uuid.uuid4(),
        strategy_id=uuid.uuid4(),
        symbol='AAPL',
        mode=RunMode.BACKTEST,
        initial_capital=100000,
        strategy_params={},
        risk_config=RiskConfig(max_pos_size=0, max_notional_per_trade=0),
        market_data_config=MarketDataConfig(
            source=MarketDataSource.historical,
            start_date=datetime.strptime("2021-07-01", "%Y-%m-%d"),
            end_date=datetime.strptime("2021-10-01", "%Y-%m-%d"),
        )
    )
    market_data_adapter = HistoricalMarketDataAdapter(credential_store, run_config = run_config)
    bars = []
    for bar in market_data_adapter.stream:
        bars.append(bar)
    return {"status": bars}

if __name__ == "__main__":
    uvicorn.run("apps.api.main:app", host="0.0.0.0", port=8080, reload=True)
