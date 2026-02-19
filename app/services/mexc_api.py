"""MEXC API client with resilience and throttling."""
from __future__ import annotations

import asyncio
import logging
from typing import Dict, List

import aiohttp

from app.config import Config
from app.utils.backoff import retry_async
from app.utils.validators import validate_interval

logger = logging.getLogger("mexc_api")

MEXC_KLINE_PATH = "/open/api/v2/market/kline"
INTERVAL_MAP = {
    "1m": 60,
    "5m": 300,
    "15m": 900,
    "30m": 1800,
    "1h": 3600,
    "4h": 14400,
    "1d": 86400,
}


class MexcClient:
    """Async client for MEXC public market data."""

    def __init__(self, config: Config) -> None:
        self._config = config
        self._session: aiohttp.ClientSession | None = None
        self._rate_lock = asyncio.Lock()
        self._last_request_ts: float = 0.0

    async def start(self) -> None:
        if self._session is None:
            timeout = aiohttp.ClientTimeout(total=self._config.mexc_timeout_seconds)
            self._session = aiohttp.ClientSession(timeout=timeout)

    async def close(self) -> None:
        if self._session:
            await self._session.close()
            self._session = None

    def _require_session(self) -> aiohttp.ClientSession:
        if not self._session:
            raise RuntimeError("MEXC session not initialized")
        return self._session

    async def get_candles(
        self, symbol: str, interval: str = "1h", limit: int = 120
    ) -> List[Dict[str, float]]:
        validate_interval(interval, INTERVAL_MAP.keys())
        url = self._config.mexc_base_url.rstrip("/") + MEXC_KLINE_PATH
        params = {"symbol": symbol, "interval": interval, "limit": limit}

        await self._throttle()

        async def _fetch() -> List[Dict[str, float]]:
            session = self._require_session()
            async with session.get(url, params=params) as resp:
                if resp.status != 200:
                    raise RuntimeError(f"MEXC HTTP {resp.status}")
                data = await resp.json()
                if data.get("code") != 200:
                    raise RuntimeError(f"MEXC error: {data}")
                candles = []
                for item in data.get("data", []):
                    candles.append(
                        {
                            "timestamp": float(item[0]),
                            "open": float(item[1]),
                            "high": float(item[2]),
                            "low": float(item[3]),
                            "close": float(item[4]),
                            "volume": float(item[5]),
                        }
                    )
                return candles

        try:
            # Retry with exponential backoff and jitter
            result = await retry_async(
                _fetch,
                retries=self._config.mexc_retries,
                base_delay=self._config.mexc_backoff_base,
                max_delay=5.0,
                retry_exceptions=(aiohttp.ClientError, asyncio.TimeoutError, RuntimeError),
            )
            return result
        except Exception as exc:
            logger.warning(
                "mexc_call_failed symbol=%s interval=%s error=%s", symbol, interval, exc
            )
            raise

    async def _throttle(self) -> None:
        """Simple rate limiting using minimum interval between requests."""
        min_interval = max(self._config.mexc_min_interval_seconds, 0.0)
        if min_interval <= 0:
            return
        async with self._rate_lock:
            now = asyncio.get_event_loop().time()
            elapsed = now - self._last_request_ts
            if elapsed < min_interval:
                await asyncio.sleep(min_interval - elapsed)
            self._last_request_ts = asyncio.get_event_loop().time()





