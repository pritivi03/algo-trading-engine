import uuid
from pathlib import Path

from dotenv import load_dotenv

from trading.persistence.db import get_session, init_db
from trading.persistence.repositories import StrategyRepository

load_dotenv()

NAMESPACE = uuid.UUID("00000000-0000-0000-0000-000000000001")
SEEDS_DIR = Path(__file__).resolve().parents[1] / "trading" / "strategies" / "seeds"


def main():
    init_db()
    seeded: list[tuple[str, uuid.UUID]] = []

    with get_session() as session:
        repo = StrategyRepository(session)
        for path in sorted(SEEDS_DIR.glob("*.py")):
            if path.name == "__init__.py":
                continue
            code = path.read_text()
            if not code.strip():
                continue
            name = path.stem
            strategy_id = uuid.uuid5(NAMESPACE, name)
            repo.upsert(strategy_id, name, code)
            seeded.append((name, strategy_id))

    print(f"Seeded {len(seeded)} strategies:")
    for name, sid in seeded:
        print(f"  {name:30s} {sid}")


if __name__ == "__main__":
    main()
