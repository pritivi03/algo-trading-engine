import uuid

from fastapi import APIRouter

from apps.api.schemas.strategies import CreateStrategyRequest, StrategyResponse
from trading.persistence.db import get_session
from trading.persistence.repositories import StrategyRepository

router = APIRouter(prefix="/strategies", tags=["strategies"])


@router.post("", response_model=StrategyResponse)
def create_strategy(req: CreateStrategyRequest) -> StrategyResponse:
    strategy_id = uuid.uuid4()
    with get_session() as session:
        row = StrategyRepository(session).save(strategy_id, req.name, req.code)
        session.flush()
        return StrategyResponse(id=row.id, name=row.name, created_at=row.created_at)


@router.get("", response_model=list[StrategyResponse])
def list_strategies() -> list[StrategyResponse]:
    with get_session() as session:
        rows = StrategyRepository(session).list_all()
        return [StrategyResponse(id=r.id, name=r.name, created_at=r.created_at) for r in rows]