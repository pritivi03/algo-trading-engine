from datetime import datetime
from uuid import UUID

from pydantic import BaseModel


class CreateStrategyRequest(BaseModel):
    name: str
    code: str


class StrategyResponse(BaseModel):
    id: UUID
    name: str
    code: str
    created_at: datetime