import uuid
from uuid import UUID

from fastapi import APIRouter, HTTPException

from apps.api.schemas.runs import CreateRunRequest, RunResponse, MetricsResponse, FillResponse, EquitySnapshotResponse
from apps.api.services import launcher
from trading.core.config import RunConfig
from trading.persistence.db import get_session
from trading.persistence.orm_models import StrategyRunRow, FillRow, RunMetricsRow
from trading.persistence.repositories import RunRepository, MetricsRepository, FillRepository, EquitySnapshotRepository

router = APIRouter(prefix="/runs", tags=["runs"])


def _to_response(row: StrategyRunRow) -> RunResponse:
    return RunResponse(
        id=row.id,
        strategy_id=row.strategy_id,
        status=row.status,
        container_id=row.container_id,
        error_message=row.error_message,
        config=row.config_json,
        created_at=row.created_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
    )


def _to_metrics_response(row: RunMetricsRow) -> MetricsResponse:
    return MetricsResponse(
        run_id=row.run_id,
        total_return_pct=row.total_return_pct,
        sharpe_ratio=row.sharpe_ratio,
        max_drawdown_pct=row.max_drawdown_pct,
        win_rate=row.win_rate,
        total_trades=row.total_trades,
        avg_win=row.avg_win,
        avg_loss=row.avg_loss,
        final_cash=row.final_cash,
        final_equity=row.final_equity,
        realized_pnl=row.realized_pnl,
        unrealized_pnl=row.unrealized_pnl,
        updated_at=row.updated_at,
    )


def _to_fill_response(row: FillRow) -> FillResponse:
    return FillResponse(
        id=row.id,
        order_id=row.order_id,
        symbol=row.symbol,
        side=row.side.value if hasattr(row.side, "value") else row.side,
        qty=row.qty,
        fill_price=row.fill_price,
        fees=row.fees,
        timestamp=row.timestamp,
    )

@router.get("", response_model=list[RunResponse])
def list_runs() -> list[RunResponse]:
    with get_session() as session:
        rows = RunRepository(session).list_all()
        return [_to_response(r) for r in rows]

@router.post("", response_model=RunResponse)
def create_run(req: CreateRunRequest) -> RunResponse:
    run_id = uuid.uuid4()
    config = RunConfig(
        run_id=run_id,
        strategy_id=req.strategy_id,
        symbol=req.symbol,
        mode=req.mode,
        initial_capital=req.initial_capital,
        strategy_params=req.strategy_params,
        risk_config=req.risk_config,
        market_data_config=req.market_data_config,
    )
    with get_session() as session:
        row = RunRepository(session).create(run_id, req.strategy_id, config)
        session.flush()
        return _to_response(row)

@router.get("/{run_id}", response_model=RunResponse)
def get_run(run_id: UUID) -> RunResponse:
    with get_session() as session:
        row = session.get(StrategyRunRow, run_id)
        if row is None:
            raise HTTPException(404, f"Run {run_id} not found")
        return _to_response(row)

@router.get("/{run_id}/metrics", response_model=MetricsResponse)
def get_metrics(run_id: UUID) -> MetricsResponse:
    with get_session() as session:
        row = MetricsRepository(session).get(run_id)
        if row is None:
            raise HTTPException(404, f"No metrics for run {run_id}")
        return _to_metrics_response(row)


@router.get("/{run_id}/fills", response_model=list[FillResponse])
def list_fills(run_id: UUID) -> list[FillResponse]:
    with get_session() as session:
        rows = FillRepository(session).get_by_run(run_id)
        return [_to_fill_response(r) for r in rows]

@router.get("/{run_id}/equity-snapshots", response_model=list[EquitySnapshotResponse])
def list_equity_snapshots(run_id: UUID) -> list[EquitySnapshotResponse]:
    with get_session() as session:
        rows = EquitySnapshotRepository(session).get_by_run(run_id)
        return [EquitySnapshotResponse(timestamp=r.timestamp, equity=r.equity, cash=r.cash) for r in rows]


@router.post("/{run_id}/start", response_model=RunResponse)
def start_run(run_id: UUID) -> RunResponse:
    with get_session() as session:
        row = session.get(StrategyRunRow, run_id)
        if row is None:
            raise HTTPException(404, f"Run {run_id} not found")
        if row.status != "pending":
            raise HTTPException(409, f"Run is in status {row.status!r}, can only start a pending run")
        run_mode = row.config_json.get("mode", "backtest")

    container_id = launcher.launch_run(run_id, mode=run_mode)

    with get_session() as session:
        RunRepository(session).set_container_id(run_id, container_id)
        row = session.get(StrategyRunRow, run_id)
        return _to_response(row)

@router.delete("/{run_id}", status_code=204)
def delete_run(run_id: UUID) -> None:
    with get_session() as session:
        row = session.get(StrategyRunRow, run_id)
        if row is None:
            raise HTTPException(404, f"Run {run_id} not found")
        if row.status not in ("completed", "failed"):
            raise HTTPException(409, f"Cannot delete a run in status {row.status!r}")
        RunRepository(session).delete(run_id)


@router.post("/{run_id}/stop", response_model=RunResponse)
def stop_run(run_id: UUID) -> RunResponse:
    with get_session() as session:
        row = session.get(StrategyRunRow, run_id)
        if row is None:
            raise HTTPException(404, f"Run {run_id} not found")
        if row.container_id is None:
            raise HTTPException(409, "Run has no container to stop")
        container_id = row.container_id

    launcher.stop_run(container_id)

    with get_session() as session:
        row = session.get(StrategyRunRow, run_id)
        return _to_response(row)
