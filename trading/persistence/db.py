import os
from contextlib import contextmanager

from sqlalchemy import create_engine, Engine
from sqlalchemy.orm import sessionmaker, Session

from trading.persistence.orm_models import Base

_engine: Engine | None = None
_SessionLocal: sessionmaker | None = None


def _get_engine() -> Engine:
    global _engine, _SessionLocal
    if _engine is None:
        url = os.environ.get("DATABASE_URL")
        if not url:
            raise RuntimeError(
                "DATABASE_URL env var not set. "
                "Make sure load_dotenv() runs before any DB operation, "
                "or export DATABASE_URL in your shell."
            )
        _engine = create_engine(url)
        _SessionLocal = sessionmaker(bind=_engine)
    return _engine


def init_db() -> None:
    Base.metadata.create_all(_get_engine())


@contextmanager
def get_session() -> Session:
    _get_engine()  # ensures _SessionLocal is initialized
    session = _SessionLocal()
    try:
        yield session
        session.commit()
    except:
        session.rollback()
        raise
    finally:
        session.close()