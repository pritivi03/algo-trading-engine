import uuid
from uuid import UUID

from fastapi import APIRouter, HTTPException

from apps.api.schemas.runs import CreateRunRequest, RunResponse
from apps.api.services import launcher
from trading.core.config import RunConfig
from trading.persistence.db import get_session
from trading.persistence.orm_models import StrategyRunRow
from trading.persistence.repositories import RunRepository

router = APIRouter(prefix="/runs", tags=["runs"])


def _to_response(row: StrategyRunRow) -> RunResponse:
    return RunResponse(
        id=row.id,
        strategy_id=row.strategy_id,
        status=row.status,
        container_id=row.container_id,
        error_message=row.error_message,
        created_at=row.created_at,
        started_at=row.started_at,
        completed_at=row.completed_at,
    )


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


@router.post("/{run_id}/start", response_model=RunResponse)
def start_run(run_id: UUID) -> RunResponse:
    with get_session() as session:
        row = session.get(StrategyRunRow, run_id)
        if row is None:
            raise HTTPException(404, f"Run {run_id} not found")
        if row.status != "pending":
            raise HTTPException(409, f"Run is in status {row.status!r}, can only start a pending run")

    container_id = launcher.launch_run(run_id)

    with get_session() as session:
        RunRepository(session).set_container_id(run_id, container_id)
        row = session.get(StrategyRunRow, run_id)
        return _to_response(row)


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