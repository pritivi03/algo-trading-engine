import inspect
import uuid
from typing import Any

from fastapi import APIRouter

from apps.api.schemas.strategies import CreateStrategyRequest, StrategyResponse
from trading.persistence.db import get_session
from trading.persistence.repositories import StrategyRepository
from trading.strategies.base import BaseStrategy

router = APIRouter(prefix="/strategies", tags=["strategies"])


def _extract_default_params(code: str) -> dict[str, Any]:
    try:
        namespace: dict[str, Any] = {}
        exec(code, namespace)
        for obj in namespace.values():
            if isinstance(obj, type) and issubclass(obj, BaseStrategy) and obj is not BaseStrategy:
                sig = inspect.signature(obj.__init__)
                return {
                    name: (param.default if param.default is not inspect.Parameter.empty else None)
                    for name, param in sig.parameters.items()
                    if name != "self"
                }
    except Exception:
        pass
    return {}


def _to_response(row: Any) -> StrategyResponse:
    return StrategyResponse(
        id=row.id,
        name=row.name,
        code=row.code,
        default_params=_extract_default_params(row.code),
        created_at=row.created_at,
    )


@router.post("", response_model=StrategyResponse)
def create_strategy(req: CreateStrategyRequest) -> StrategyResponse:
    strategy_id = uuid.uuid4()
    with get_session() as session:
        row = StrategyRepository(session).save(strategy_id, req.name, req.code)
        session.flush()
        return _to_response(row)


@router.get("", response_model=list[StrategyResponse])
def list_strategies() -> list[StrategyResponse]:
    with get_session() as session:
        rows = StrategyRepository(session).list_all()
        return [_to_response(r) for r in rows]


@router.get("/{strategy_id}", response_model=StrategyResponse)
def get_strategy(strategy_id: uuid.UUID) -> StrategyResponse:
    with get_session() as session:
        row = StrategyRepository(session).get(strategy_id)
        return _to_response(row)


@router.put("/{strategy_id}", response_model=StrategyResponse)
def update_strategy(strategy_id: uuid.UUID, req: CreateStrategyRequest) -> StrategyResponse:
    with get_session() as session:
        row = StrategyRepository(session).update(strategy_id, req.name, req.code)
        return _to_response(row)
