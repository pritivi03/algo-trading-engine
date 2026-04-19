from typing import Any

from trading.strategies.base import BaseStrategy


def load_strategy_from_code(code: str, params: dict[str, Any]) -> BaseStrategy:
    namespace: dict[str, Any] = {}
    exec(code, namespace)

    for obj in namespace.values():
        if (
            isinstance(obj, type)
            and issubclass(obj, BaseStrategy)
            and obj is not BaseStrategy
        ):
            return obj(**params)

    raise ValueError("No BaseStrategy subclass found in strategy code")