import os
from uuid import UUID

import docker
import docker.errors

RUNTIME_IMAGE = "algo-trading-runtime:latest"


def _runtime_database_url() -> str:
    # Env override exists because when the API runs locally, its own DATABASE_URL
    # points at localhost:5432, but a runtime *container* needs to reach Postgres
    # via the docker network hostname (`db:5432`).
    return os.environ.get(
        "RUNTIME_DATABASE_URL",
        "postgresql://algo:secret@db:5432/algo_trading",
    )


def _runtime_network() -> str:
    return os.environ.get("RUNTIME_NETWORK", "docker_default")


def launch_run(run_id: UUID) -> str:
    client = docker.from_env()
    container = client.containers.run(
        image=RUNTIME_IMAGE,
        name=f"run-{run_id}",
        environment={
            "RUN_ID": str(run_id),
            "DATABASE_URL": _runtime_database_url(),
            "ALPACA_API_KEY": os.environ["ALPACA_API_KEY"],
            "ALPACA_SECRET_KEY": os.environ["ALPACA_SECRET_KEY"],
        },
        network=_runtime_network(),
        detach=True,
    )
    return container.id


def stop_run(container_id: str) -> None:
    client = docker.from_env()
    try:
        container = client.containers.get(container_id)
        container.stop(timeout=10)
    except docker.errors.NotFound:
        pass


def container_status(container_id: str) -> str | None:
    client = docker.from_env()
    try:
        return client.containers.get(container_id).status
    except docker.errors.NotFound:
        return None