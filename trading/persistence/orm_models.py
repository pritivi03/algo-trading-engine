from datetime import datetime
from uuid import UUID

from sqlalchemy import String, Float, Integer, DateTime, Enum as SAEnum, ForeignKey
from sqlalchemy.dialects.postgresql import UUID as PGUUID, JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column
from sqlalchemy.sql import func

from trading.core.enums import Side, OrderStatus


class Base(DeclarativeBase):
    pass


class StrategyRow(Base):
    __tablename__ = "strategies"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    name: Mapped[str] = mapped_column(String, nullable=False)
    code: Mapped[str] = mapped_column(String, nullable=False)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())


class StrategyRunRow(Base):
    __tablename__ = "strategy_runs"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    strategy_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("strategies.id"), nullable=False)
    status: Mapped[str] = mapped_column(String, nullable=False, default="pending")  # pending | running | completed | failed
    config_json: Mapped[dict] = mapped_column(JSONB, nullable=False)
    container_id: Mapped[str | None] = mapped_column(String, nullable=True)
    error_message: Mapped[str | None] = mapped_column(String, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now())
    started_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)
    completed_at: Mapped[datetime | None] = mapped_column(DateTime, nullable=True)


class FillRow(Base):
    __tablename__ = "fills"

    id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), primary_key=True)
    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("strategy_runs.id"), nullable=False, index=True)
    order_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), nullable=False)
    symbol: Mapped[str] = mapped_column(String, nullable=False)
    side: Mapped[str] = mapped_column(SAEnum(Side), nullable=False)
    qty: Mapped[int] = mapped_column(Integer, nullable=False)
    fill_price: Mapped[float] = mapped_column(Float, nullable=False)
    fees: Mapped[float] = mapped_column(Float, nullable=False)
    timestamp: Mapped[datetime] = mapped_column(DateTime, nullable=False)


class RunMetricsRow(Base):
    __tablename__ = "run_metrics"

    run_id: Mapped[UUID] = mapped_column(PGUUID(as_uuid=True), ForeignKey("strategy_runs.id"), primary_key=True)
    total_return_pct: Mapped[float] = mapped_column(Float, nullable=False)
    sharpe_ratio: Mapped[float] = mapped_column(Float, nullable=False)
    max_drawdown_pct: Mapped[float] = mapped_column(Float, nullable=False)
    win_rate: Mapped[float] = mapped_column(Float, nullable=False)
    total_trades: Mapped[int] = mapped_column(Integer, nullable=False)
    avg_win: Mapped[float] = mapped_column(Float, nullable=False)
    avg_loss: Mapped[float] = mapped_column(Float, nullable=False)
    updated_at: Mapped[datetime] = mapped_column(DateTime, server_default=func.now(), onupdate=func.now())