from __future__ import annotations

import asyncio
import logging
import os
from typing import Any

import aiohttp
from fastapi import FastAPI, Header, HTTPException

from app.config import Config
from app.utils.backoff import retry_async

logger = logging.getLogger("trader_bridge")


class TraderBridge:
    """Optional webhook bridge for auto-trader integration (client)."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._session: aiohttp.ClientSession | None = None

    @property
    def enabled(self) -> bool:
        return self._config.enable_trader_bridge

    async def start(self) -> None:
        if self.enabled and self._session is None:
            timeout = aiohttp.ClientTimeout(total=self._config.trader_bridge_timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    def _require_session(self) -> aiohttp.ClientSession:
        if not self._session:
            raise RuntimeError("TraderBridge session not initialized")
        return self._session

    async def send_signal(self, payload: dict[str, Any]) -> bool:
        """Send payload to configured webhook. Returns True if delivered."""
        if not self.enabled:
            return False

        url = self._config.trader_bridge_url
        if not url:
            return False

        headers = {}
        if self._config.trader_bridge_token:
            headers["Authorization"] = f"Bearer {self._config.trader_bridge_token}"

        async def _post() -> bool:
            session = self._require_session()
            async with session.post(url, json=payload, headers=headers) as resp:
                if resp.status >= 400:
                    body = await resp.text()
                    raise RuntimeError(f"Bridge HTTP {resp.status}: {body}")
                return True

        try:
            result = await retry_async(
                _post,
                retries=self._config.trader_bridge_retries,
                base_delay=self._config.trader_bridge_backoff_base,
                max_delay=5.0,
                retry_exceptions=(aiohttp.ClientError, asyncio.TimeoutError, RuntimeError),
            )
            return bool(result)
        except Exception as exc:
            logger.warning("Trader bridge failed: %s", exc)
            return False


def create_bridge_app(shared_secret: str | None = None) -> FastAPI:
    """Create a minimal FastAPI webhook receiver for external auto-traders."""

    app = FastAPI(title="Trader Bridge", version="1.0.0")

    @app.post("/webhook")
    async def webhook(
        payload: dict[str, Any],
        x_bridge_token: str | None = Header(default=None, alias="X-Bridge-Token"),
    ) -> dict[str, Any]:
        if shared_secret:
            if not x_bridge_token or x_bridge_token != shared_secret:
                raise HTTPException(status_code=401, detail="Invalid bridge token")
        # In a real implementation, forward payload to a trading engine.
        logger.info("Bridge payload received: %s", payload.get("type"))
        return {"status": "ok"}

    return app


def create_app() -> FastAPI:
    """Factory for `uvicorn app.services.optional_bridge:create_app --factory`."""
    enabled = os.getenv("ENABLE_TRADER_BRIDGE", "").strip().lower() in {
        "1",
        "true",
        "yes",
        "y",
        "on",
    }
    if not enabled:
        raise RuntimeError("ENABLE_TRADER_BRIDGE must be true to run the bridge receiver")
    secret = os.getenv("TRADER_BRIDGE_TOKEN", "").strip() or None
    return create_bridge_app(secret)
