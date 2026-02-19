from __future__ import annotations

from dataclasses import dataclass
import os
from typing import List, Set

from dotenv import load_dotenv

from app.utils.validators import (
    parse_bool,
    parse_coins_list,
    parse_csv,
    parse_float,
    parse_int,
)


def _parse_admins(raw: str) -> Set[int]:
    admins: Set[int] = set()
    for item in parse_csv(raw):
        try:
            admins.add(int(item))
        except ValueError:
            continue
    return admins


@dataclass
class Config:
    """Runtime configuration loaded from environment."""

    bot_token: str
    db_host: str
    db_port: int
    db_user: str
    db_password: str
    db_name: str

    timeframe: str
    spot_cycle_seconds: int
    futures_breakout_seconds: int
    futures_breakout_lookback: int
    futures_breakout_cooldown_seconds: int

    default_free_limit: int
    admins: Set[int]
    coins_list: List[str]

    log_level: str
    log_dir: str | None
    log_retention_days: int

    mexc_base_url: str
    mexc_timeout_seconds: int
    mexc_retries: int
    mexc_backoff_base: float
    mexc_min_interval_seconds: float

    telegram_retries: int
    telegram_backoff_base: float
    telegram_send_delay_seconds: float
    broadcast_cooldown_seconds: int
    broadcast_duplicate_window_seconds: int

    enable_spot_cycle: bool
    enable_futures_breakout: bool
    enable_daily_reset: bool
    enable_trader_bridge: bool

    trader_bridge_url: str | None
    trader_bridge_token: str | None
    trader_bridge_timeout_seconds: int
    trader_bridge_retries: int
    trader_bridge_backoff_base: float


def load_config() -> Config:
    load_dotenv()

    errors: list[str] = []

    bot_token = os.getenv("BOT_TOKEN", "").strip()
    if not bot_token:
        errors.append("BOT_TOKEN is required")

    db_host = os.getenv("DB_HOST", "localhost")
    db_port = parse_int(os.getenv("DB_PORT"), 3306)
    db_user = os.getenv("DB_USER", "root")
    db_password = os.getenv("DB_PASSWORD", "").strip()
    if not db_password:
        errors.append("DB_PASSWORD is required")
    db_name = os.getenv("DB_NAME", "crypto_bot")

    timeframe = os.getenv("TIMEFRAME", "1h")
    spot_cycle_seconds = parse_int(os.getenv("SPOT_CYCLE_SECONDS"), 3600)
    futures_breakout_seconds = parse_int(os.getenv("FUTURES_BREAKOUT_SECONDS"), 30)
    futures_breakout_lookback = parse_int(os.getenv("FUTURES_BREAKOUT_LOOKBACK"), 3)
    futures_breakout_cooldown_seconds = parse_int(
        os.getenv("FUTURES_BREAKOUT_COOLDOWN_SECONDS"), 300
    )

    default_free_limit = parse_int(os.getenv("DEFAULT_FREE_LIMIT"), 2)
    admins = _parse_admins(os.getenv("ADMINS", ""))
    try:
        coins_list = parse_coins_list(os.getenv("COINS_LIST", "BTC_USDT,ETH_USDT"))
    except ValueError as exc:
        errors.append(str(exc))
        coins_list = ["BTC_USDT"]

    log_level = os.getenv("LOG_LEVEL", "INFO")
    log_dir = os.getenv("LOG_DIR", "logs") or None
    log_retention_days = parse_int(os.getenv("LOG_RETENTION_DAYS"), 14)

    mexc_base_url = os.getenv("MEXC_BASE_URL", "https://www.mexc.com")
    mexc_timeout_seconds = parse_int(os.getenv("MEXC_TIMEOUT_SECONDS"), 15)
    mexc_retries = parse_int(os.getenv("MEXC_RETRIES"), 3)
    mexc_backoff_base = parse_float(os.getenv("MEXC_BACKOFF_BASE"), 0.5)
    mexc_min_interval_seconds = parse_float(os.getenv("MEXC_MIN_INTERVAL_SECONDS"), 0.1)

    telegram_retries = parse_int(os.getenv("TELEGRAM_RETRIES"), 2)
    telegram_backoff_base = parse_float(os.getenv("TELEGRAM_BACKOFF_BASE"), 0.5)
    telegram_send_delay_seconds = parse_float(os.getenv("TELEGRAM_SEND_DELAY_SECONDS"), 0.2)
    broadcast_cooldown_seconds = parse_int(os.getenv("BROADCAST_COOLDOWN_SECONDS"), 60)
    broadcast_duplicate_window_seconds = parse_int(
        os.getenv("BROADCAST_DUPLICATE_WINDOW_SECONDS"), 300
    )

    enable_spot_cycle = parse_bool(os.getenv("ENABLE_SPOT_CYCLE"), True)
    enable_futures_breakout = parse_bool(os.getenv("ENABLE_FUTURES_BREAKOUT"), True)
    enable_daily_reset = parse_bool(os.getenv("ENABLE_DAILY_RESET"), True)
    enable_trader_bridge = parse_bool(os.getenv("ENABLE_TRADER_BRIDGE"), False)

    trader_bridge_url = os.getenv("TRADER_BRIDGE_URL") if enable_trader_bridge else None
    trader_bridge_token = os.getenv("TRADER_BRIDGE_TOKEN") if enable_trader_bridge else None
    trader_bridge_timeout_seconds = parse_int(os.getenv("TRADER_BRIDGE_TIMEOUT_SECONDS"), 10)
    trader_bridge_retries = parse_int(os.getenv("TRADER_BRIDGE_RETRIES"), 2)
    trader_bridge_backoff_base = parse_float(os.getenv("TRADER_BRIDGE_BACKOFF_BASE"), 0.5)

    if enable_trader_bridge and not trader_bridge_url:
        errors.append("ENABLE_TRADER_BRIDGE is true but TRADER_BRIDGE_URL is missing")

    if spot_cycle_seconds <= 0:
        errors.append("SPOT_CYCLE_SECONDS must be > 0")
    if futures_breakout_seconds <= 0:
        errors.append("FUTURES_BREAKOUT_SECONDS must be > 0")
    if futures_breakout_lookback <= 0:
        errors.append("FUTURES_BREAKOUT_LOOKBACK must be > 0")
    if default_free_limit < 0:
        errors.append("DEFAULT_FREE_LIMIT must be >= 0")
    if mexc_timeout_seconds <= 0:
        errors.append("MEXC_TIMEOUT_SECONDS must be > 0")
    if mexc_retries < 0:
        errors.append("MEXC_RETRIES must be >= 0")
    if mexc_min_interval_seconds < 0:
        errors.append("MEXC_MIN_INTERVAL_SECONDS must be >= 0")
    if telegram_retries < 0:
        errors.append("TELEGRAM_RETRIES must be >= 0")
    if telegram_send_delay_seconds < 0:
        errors.append("TELEGRAM_SEND_DELAY_SECONDS must be >= 0")
    if broadcast_cooldown_seconds < 0:
        errors.append("BROADCAST_COOLDOWN_SECONDS must be >= 0")
    if broadcast_duplicate_window_seconds < 0:
        errors.append("BROADCAST_DUPLICATE_WINDOW_SECONDS must be >= 0")
    if log_retention_days < 14:
        errors.append("LOG_RETENTION_DAYS must be >= 14")

    if errors:
        raise RuntimeError("Config validation failed: " + "; ".join(errors))

    return Config(
        bot_token=bot_token,
        db_host=db_host,
        db_port=db_port,
        db_user=db_user,
        db_password=db_password,
        db_name=db_name,
        timeframe=timeframe,
        spot_cycle_seconds=spot_cycle_seconds,
        futures_breakout_seconds=futures_breakout_seconds,
        futures_breakout_lookback=futures_breakout_lookback,
        futures_breakout_cooldown_seconds=futures_breakout_cooldown_seconds,
        default_free_limit=default_free_limit,
        admins=admins,
        coins_list=coins_list,
        log_level=log_level,
        log_dir=log_dir,
        log_retention_days=log_retention_days,
        mexc_base_url=mexc_base_url,
        mexc_timeout_seconds=mexc_timeout_seconds,
        mexc_retries=mexc_retries,
        mexc_backoff_base=mexc_backoff_base,
        mexc_min_interval_seconds=mexc_min_interval_seconds,
        telegram_retries=telegram_retries,
        telegram_backoff_base=telegram_backoff_base,
        telegram_send_delay_seconds=telegram_send_delay_seconds,
        broadcast_cooldown_seconds=broadcast_cooldown_seconds,
        broadcast_duplicate_window_seconds=broadcast_duplicate_window_seconds,
        enable_spot_cycle=enable_spot_cycle,
        enable_futures_breakout=enable_futures_breakout,
        enable_daily_reset=enable_daily_reset,
        enable_trader_bridge=enable_trader_bridge,
        trader_bridge_url=trader_bridge_url,
        trader_bridge_token=trader_bridge_token,
        trader_bridge_timeout_seconds=trader_bridge_timeout_seconds,
        trader_bridge_retries=trader_bridge_retries,
        trader_bridge_backoff_base=trader_bridge_backoff_base,
    )


def reload_coins(config: Config, new_value: str | None = None) -> List[str]:
    """Reload coins list either from a provided string or from env."""
    if new_value is None:
        load_dotenv(override=True)
    raw = new_value if new_value is not None else os.getenv("COINS_LIST", "")
    coins = parse_coins_list(raw)
    config.coins_list = coins
    return coins
