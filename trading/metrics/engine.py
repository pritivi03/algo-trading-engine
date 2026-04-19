import math
from dataclasses import dataclass

from trading.core.enums import Side
from trading.core.events import FillEvent
from trading.core.models import FillResult


@dataclass
class RunMetrics:
    total_return_pct: float
    sharpe_ratio: float
    max_drawdown_pct: float
    win_rate: float
    total_trades: int
    avg_win: float
    avg_loss: float


_ANNUALIZATION_FACTORS = {
    "minute": math.sqrt(390 * 252),
    "hour": math.sqrt(int(6.5 * 252)),
    "day": math.sqrt(252),
}


class MetricsEngine:
    def __init__(self, initial_equity: float, timeframe: str = "minute"):
        self.initial_equity = initial_equity
        self.ANNUALIZATION_FACTOR = _ANNUALIZATION_FACTORS.get(timeframe, _ANNUALIZATION_FACTORS["minute"])

        # drawdown tracking
        self.peak_equity = initial_equity
        self.max_drawdown = 0.0

        # Welford's online algorithm for Sharpe
        self.n = 0
        self.mean_return = 0.0
        self.m2_return = 0.0
        self.prev_equity = initial_equity

        # trade tracking
        self.total_trades = 0
        self.winning_trades = 0
        self.total_win_amount = 0.0
        self.total_loss_amount = 0.0

    def on_bar(self, equity: float) -> None:
        if self.prev_equity > 0:
            period_return = (equity - self.prev_equity) / self.prev_equity
            self.n += 1
            delta = period_return - self.mean_return
            self.mean_return += delta / self.n
            delta2 = period_return - self.mean_return
            self.m2_return += delta * delta2

        self.peak_equity = max(self.peak_equity, equity)
        if self.peak_equity > 0:
            drawdown = (self.peak_equity - equity) / self.peak_equity
            self.max_drawdown = max(self.max_drawdown, drawdown)

        self.prev_equity = equity

    def on_fill(self, fill: FillEvent, result: FillResult) -> None:
        if fill.side == Side.SELL:
            self.total_trades += 1
            if result.realized_pnl > 0:
                self.winning_trades += 1
                self.total_win_amount += result.realized_pnl
            else:
                self.total_loss_amount += result.realized_pnl

    def summary(self, final_equity: float) -> RunMetrics:
        total_return_pct = (final_equity - self.initial_equity) / self.initial_equity * 100

        if self.n > 1 and self.m2_return > 0:
            std_return = math.sqrt(self.m2_return / (self.n - 1))
            sharpe = (self.mean_return / std_return) * self.ANNUALIZATION_FACTOR
        else:
            sharpe = 0.0

        losing_trades = self.total_trades - self.winning_trades
        win_rate = self.winning_trades / self.total_trades if self.total_trades > 0 else 0.0
        avg_win = self.total_win_amount / self.winning_trades if self.winning_trades > 0 else 0.0
        avg_loss = self.total_loss_amount / losing_trades if losing_trades > 0 else 0.0

        return RunMetrics(
            total_return_pct=total_return_pct,
            sharpe_ratio=sharpe,
            max_drawdown_pct=self.max_drawdown * 100,
            win_rate=win_rate,
            total_trades=self.total_trades,
            avg_win=avg_win,
            avg_loss=avg_loss,
        )