from __future__ import annotations

from typing import Iterable, List


def parse_int(value: str | None, default: int) -> int:
    if value is None or str(value).strip() == "":
        return default
    try:
        return int(value)
    except (TypeError, ValueError):
        return default


def parse_float(value: str | None, default: float) -> float:
    if value is None or str(value).strip() == "":
        return default
    try:
        return float(value)
    except (TypeError, ValueError):
        return default


def parse_bool(value: str | None, default: bool = False) -> bool:
    if value is None:
        return default
    normalized = value.strip().lower()
    if normalized in {"1", "true", "yes", "y", "on"}:
        return True
    if normalized in {"0", "false", "no", "n", "off"}:
        return False
    return default


def parse_csv(value: str | None) -> List[str]:
    if not value:
        return []
    return [item.strip() for item in value.split(",") if item.strip()]


def validate_role(role: str) -> str:
    role = (role or "").lower().strip()
    if role not in {"free", "vip", "extreme"}:
        raise ValueError("role must be free/vip/extreme")
    return role


def validate_interval(interval: str, allowed: Iterable[str]) -> str:
    if interval not in allowed:
        raise ValueError(f"Invalid interval: {interval}")
    return interval


def parse_coins_list(raw: str | None) -> List[str]:
    coins = parse_csv(raw)
    if not coins:
        raise ValueError("COINS_LIST must include at least one symbol")
    return coins
