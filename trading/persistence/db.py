import os
from collections.abc import Generator
from contextlib import contextmanager
from typing import cast

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from trading.persistence.orm_models import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker[Session] | None = None

def _get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None or _SessionLocal is None:
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError(
                "DATABASE_URL env var not set. "
                "Make sure load_dotenv() runs before any DB operation, "
                "or export DATABASE_URL in your shell."
            )
        _engine = create_engine(url)
        _SessionLocal = sessionmaker(bind=_engine)
    assert _engine is not None
    return _engine


def init_db() -> None:
    Base.metadata.create_all(_get_engine())


@contextmanager
def get_session() -> Generator[Session, None, None]:
    _get_engine()  # ensures _SessionLocal is initialized
    if _SessionLocal is None:
        raise RuntimeError("Session factory not initialized")
    factory = cast(sessionmaker[Session], _SessionLocal)
    with factory() as session, session.begin():
        yield session