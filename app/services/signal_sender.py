"""Telegram message sending with retries, throttling, and safeguards."""
from __future__ import annotations

import asyncio
import logging
import time
from datetime import datetime
from typing import Set

from aiogram import Bot

from app.config import Config
from app.db.database import Database

try:  # aiogram-specific exceptions
    from aiogram.exceptions import TelegramForbiddenError, TelegramNetworkError, TelegramRetryAfter
except Exception:  # pragma: no cover - fallback for unexpected imports
    TelegramForbiddenError = type("TelegramForbiddenError", (Exception,), {})
    TelegramNetworkError = type("TelegramNetworkError", (Exception,), {})
    TelegramRetryAfter = type("TelegramRetryAfter", (Exception,), {})

logger = logging.getLogger("signal_sender")


class SignalSender:
    """Send messages with retries, throttling, and cooldowns."""

    def __init__(self, bot: Bot, db: Database, config: Config) -> None:
        self._bot = bot
        self._db = db
        self._config = config
        self._last_broadcast_at: float = 0.0
        self._last_broadcast_hash: int | None = None

    async def _send_message(self, telegram_id: int, text: str) -> None:
        retries = max(self._config.telegram_retries, 0)
        base_delay = max(self._config.telegram_backoff_base, 0.1)
        last_exc: Exception | None = None

        for attempt in range(retries + 1):
            try:
                await self._bot.send_message(telegram_id, text)
                return
            except TelegramForbiddenError as exc:
                raise exc
            except TelegramRetryAfter as exc:
                # Respect Telegram rate limiting guidance
                retry_after = getattr(exc, "retry_after", 1)
                await asyncio.sleep(retry_after)
                last_exc = exc
            except (TelegramNetworkError, Exception) as exc:
                last_exc = exc

            if attempt < retries:
                delay = min(5.0, base_delay * (2 ** attempt))
                await asyncio.sleep(delay)

        if last_exc:
            raise last_exc
        raise RuntimeError("send_message failed without exception")

    async def send_to_role(self, role: str, coin: str, s_type: str, text: str) -> int:
        users = await self._db.fetch_active_users_by_role(role)
        sent = 0

        for u in users:
            # Role filtering + expiration enforcement.
            if self._is_expired(u):
                continue
            daily_limit = int(u.get("daily_free_limit") or 0)
            if role == "free" and daily_limit <= 0:
                continue

            telegram_id = int(u["telegram_id"])
            try:
                await self._send_message(telegram_id, text)
                sent += 1
                if role == "free":
                    await self._db.decrease_free_limit(telegram_id)
            except TelegramForbiddenError:
                logger.info("User %s blocked the bot", telegram_id)
            except Exception as exc:
                logger.warning("Send failed to %s: %s", telegram_id, exc)

            delay = self._config.telegram_send_delay_seconds
            if delay > 0:
                await asyncio.sleep(delay)

        if sent > 0:
            await self._db.log_signal(coin, s_type, text, role)
        return sent

    async def broadcast(self, text: str) -> int:
        now = time.monotonic()
        if now - self._last_broadcast_at < self._config.broadcast_cooldown_seconds:
            raise RuntimeError("Broadcast cooldown active. Try again later.")
        # Anti-duplicate protection for broadcasts.
        if self._is_duplicate_broadcast(text, now):
            raise RuntimeError("Duplicate broadcast detected. Try again later.")

        users = await self._db.fetch_all_active_users()
        seen: Set[int] = set()
        sent = 0

        for u in users:
            # Role filtering + expiration enforcement.
            if self._is_expired(u):
                continue
            telegram_id = int(u["telegram_id"])
            if telegram_id in seen:
                continue
            seen.add(telegram_id)
            try:
                await self._send_message(telegram_id, text)
                sent += 1
            except TelegramForbiddenError:
                logger.info("User %s blocked the bot", telegram_id)
            except Exception as exc:
                logger.warning("Broadcast failed to %s: %s", telegram_id, exc)

            delay = self._config.telegram_send_delay_seconds
            if delay > 0:
                await asyncio.sleep(delay)

        self._last_broadcast_at = now
        self._last_broadcast_hash = hash(text)
        return sent

    def _is_expired(self, user: dict) -> bool:
        expire_at = user.get("expire_at")
        if expire_at is None:
            return False
        if isinstance(expire_at, datetime):
            return expire_at <= datetime.now()
        return False

    def _is_duplicate_broadcast(self, text: str, now: float) -> bool:
        window = self._config.broadcast_duplicate_window_seconds
        if window <= 0:
            return False
        if self._last_broadcast_hash is None:
            return False
        if hash(text) != self._last_broadcast_hash:
            return False
        return now - self._last_broadcast_at < window





