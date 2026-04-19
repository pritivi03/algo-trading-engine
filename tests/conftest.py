import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

import trading.persistence.db as _db
from trading.persistence.orm_models import FillRow, EquitySnapshotRow


@pytest.fixture()
def test_db(monkeypatch, tmp_path):
    """
    Patch the DB module to use a temporary SQLite database for the duration of
    a single test. Only creates the two tables the backtest engine writes to
    (fills + equity_snapshots); both are free of PostgreSQL-specific JSONB columns.
    SQLite doesn't enforce FK constraints by default, so fill rows can be inserted
    without corresponding strategy_run rows.
    """
    engine = create_engine(
        f"sqlite:///{tmp_path}/test.db",
        connect_args={"check_same_thread": False},
    )
    FillRow.__table__.create(engine)
    EquitySnapshotRow.__table__.create(engine)
    Session = sessionmaker(bind=engine)

    monkeypatch.setattr(_db, "_engine", engine)
    monkeypatch.setattr(_db, "_SessionLocal", Session)

    yield engine

    engine.dispose()