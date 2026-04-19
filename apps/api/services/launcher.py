import os
from uuid import UUID

import docker
import docker.errors

RUNTIME_IMAGE = "algo-trading-runtime:latest"


def _runtime_database_url() -> str:
    return os.environ.get(
        "RUNTIME_DATABASE_URL",
        "postgresql://algo:secret@db:5432/algo_trading",
    )


def _runtime_network() -> str:
    return os.environ.get("RUNTIME_NETWORK", "docker_default")


def launch_run(run_id: UUID, mode: str = "backtest") -> str:
    client = docker.from_env()
    is_live = mode in ("paper", "live")

    if mode == "paper":
        alpaca_key = os.environ["ALPACA_PAPER_API_KEY"]
        alpaca_secret = os.environ["ALPACA_PAPER_SECRET_KEY"]
    else:
        alpaca_key = os.environ["ALPACA_API_KEY"]
        alpaca_secret = os.environ["ALPACA_SECRET_KEY"]

    container = client.containers.run(
        image=RUNTIME_IMAGE,
        name=f"run-{run_id}",
        environment={
            "RUN_ID": str(run_id),
            "DATABASE_URL": _runtime_database_url(),
            "ALPACA_API_KEY": alpaca_key,
            "ALPACA_SECRET_KEY": alpaca_secret,
        },
        network=_runtime_network(),
        detach=True,
        auto_remove=not is_live,  # live/paper containers must persist until stopped
    )
    assert container.id is not None
    return container.id


def stop_run(container_id: str) -> None:
    client = docker.from_env()
    try:
        container = client.containers.get(container_id)
        container.stop(timeout=15)  # give runner time to write final metrics
        try:
            container.remove()
        except (docker.errors.NotFound, docker.errors.APIError):
            pass
    except docker.errors.NotFound:
        pass


def container_status(container_id: str) -> str | None:
    client = docker.from_env()
    try:
        return client.containers.get(container_id).status
    except docker.errors.NotFound:
        return None