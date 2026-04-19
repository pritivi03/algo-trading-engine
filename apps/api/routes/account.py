import os

from alpaca.trading.client import TradingClient
from fastapi import APIRouter
from pydantic import BaseModel

router = APIRouter(prefix="/account", tags=["account"])


class BalanceResponse(BaseModel):
    portfolio_value: float
    cash: float


@router.get("/balance", response_model=BalanceResponse)
def get_balance(paper: bool = True) -> BalanceResponse:
    if paper:
        key = os.environ["ALPACA_PAPER_API_KEY"]
        secret = os.environ["ALPACA_PAPER_SECRET_KEY"]
    else:
        key = os.environ["ALPACA_API_KEY"]
        secret = os.environ["ALPACA_SECRET_KEY"]

    client = TradingClient(key, secret, paper=paper)
    account = client.get_account()
    return BalanceResponse(
        portfolio_value=float(account.portfolio_value),
        cash=float(account.cash),
    )