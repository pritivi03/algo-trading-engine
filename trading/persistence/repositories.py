from datetime import datetime, timezone
from uuid import UUID

from sqlalchemy.orm import Session

from trading.core.config import RunConfig
from trading.core.events import FillEvent
from trading.metrics.engine import RunMetrics
from trading.persistence.orm_models import StrategyRunRow, FillRow, RunMetricsRow, StrategyRow


class StrategyRepository:
    def __init__(self, session: Session):
        self.session = session

    def get(self, strategy_id: UUID) -> StrategyRow:
        row = self.session.get(StrategyRow, strategy_id)
        if row is None:
            raise ValueError(f"Strategy {strategy_id} not found")
        return row

    def get_by_name(self, name: str) -> StrategyRow:
        row = self.session.query(StrategyRow).filter(StrategyRow.name == name).one_or_none()
        if row is None:
            raise ValueError(f"Strategy with name {name!r} not found")
        return row

    def list_all(self) -> list[StrategyRow]:
        return self.session.query(StrategyRow).all()

    def save(self, strategy_id: UUID, name: str, code: str) -> StrategyRow:
        row = StrategyRow(id=strategy_id, name=name, code=code)
        self.session.add(row)
        return row

    def upsert(self, strategy_id: UUID, name: str, code: str) -> StrategyRow:
        return self.session.merge(StrategyRow(id=strategy_id, name=name, code=code))


class RunRepository:
    def __init__(self, session: Session):
        self.session = session

    def create(self, run_id: UUID, strategy_id: UUID, config: RunConfig) -> StrategyRunRow:
        row = StrategyRunRow(
            id=run_id,
            strategy_id=strategy_id,
            status="pending",
            config_json=config.model_dump(mode="json"),
        )
        self.session.add(row)
        return row

    def load_config(self, run_id: UUID) -> RunConfig:
        row = self.session.get(StrategyRunRow, run_id)
        if row is None:
            raise ValueError(f"Run {run_id} not found")
        return RunConfig.model_validate(row.config_json)

    def mark_started(self, run_id: UUID) -> None:
        row = self.session.get(StrategyRunRow, run_id)
        row.status = "running"
        row.started_at = datetime.now(timezone.utc)

    def mark_completed(self, run_id: UUID) -> None:
        row = self.session.get(StrategyRunRow, run_id)
        row.status = "completed"
        row.completed_at = datetime.now(timezone.utc)

    def mark_failed(self, run_id: UUID, error_message: str | None = None) -> None:
        row = self.session.get(StrategyRunRow, run_id)
        row.status = "failed"
        row.completed_at = datetime.now(timezone.utc)
        if error_message is not None:
            row.error_message = error_message

    def set_container_id(self, run_id: UUID, container_id: str) -> None:
        row = self.session.get(StrategyRunRow, run_id)
        row.container_id = container_id


class FillRepository:
    def __init__(self, session: Session):
        self.session = session

    def _to_row(self, run_id: UUID, fill: FillEvent) -> FillRow:
        return FillRow(
            id=fill.fill_id,
            run_id=run_id,
            order_id=fill.order_id,
            symbol=fill.symbol,
            side=fill.side,
            qty=fill.qty,
            fill_price=fill.fill_price,
            fees=fill.fees,
            timestamp=fill.timestamp,
        )

    def save_fill(self, run_id: UUID, fill: FillEvent) -> None:
        self.session.add(self._to_row(run_id, fill))

    def save_fills_batch(self, run_id: UUID, fills: list[FillEvent]) -> None:
        self.session.add_all([self._to_row(run_id, f) for f in fills])

    def get_by_run(self, run_id: UUID) -> list[FillRow]:
        return self.session.query(FillRow).filter(FillRow.run_id == run_id).all()


class MetricsRepository:
    def __init__(self, session: Session):
        self.session = session

    def save_metrics(self, run_id: UUID, metrics: RunMetrics) -> None:
        row = RunMetricsRow(
            run_id=run_id,
            total_return_pct=metrics.total_return_pct,
            sharpe_ratio=metrics.sharpe_ratio,
            max_drawdown_pct=metrics.max_drawdown_pct,
            win_rate=metrics.win_rate,
            total_trades=metrics.total_trades,
            avg_win=metrics.avg_win,
            avg_loss=metrics.avg_loss,
        )
        self.session.merge(row)