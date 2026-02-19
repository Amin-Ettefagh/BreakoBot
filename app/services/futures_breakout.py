"""Futures breakout watcher for Extreme users."""
from __future__ import annotations

import asyncio
import logging
import time
from typing import Dict, Optional, Tuple

from app.config import Config
from app.services.mexc_api import MexcClient
from app.services.optional_bridge import TraderBridge
from app.services.signal_formatter import format_breakout_signal
from app.services.signal_sender import SignalSender

logger = logging.getLogger("futures_breakout")


class FuturesBreakoutWatcher:
    """Check 1m candles and send breakout alerts to Extreme users."""

    def __init__(
        self,
        config: Config,
        mexc: MexcClient,
        sender: SignalSender,
        bridge: TraderBridge,
    ) -> None:
        self._config = config
        self._mexc = mexc
        self._sender = sender
        self._bridge = bridge
        self._already_alerted: Dict[str, Tuple[float, float]] = {}

    async def check_breakout(self, symbol: str) -> Optional[str]:
        lookback = self._config.futures_breakout_lookback
        candles = await self._mexc.get_candles(symbol, "1m", limit=lookback + 3)
        if len(candles) < lookback + 1:
            return None

        last_close = float(candles[-1]["close"])
        prev_high = max(float(c["high"]) for c in candles[-(lookback + 1) : -1])

        if last_close <= prev_high:
            return None

        now = time.monotonic()
        # Anti-duplicate logic: prevent repeated alerts for same price within cooldown.
        last = self._already_alerted.get(symbol)
        if last:
            last_price, last_time = last
            if last_close == last_price:
                return None
            if now - last_time < self._config.futures_breakout_cooldown_seconds:
                return None

        self._already_alerted[symbol] = (last_close, now)
        return format_breakout_signal(symbol, last_close, prev_high, lookback)

    async def run_loop(self) -> None:
        while True:
            for symbol in self._config.coins_list:
                try:
                    text = await self.check_breakout(symbol)
                    if text:
                        await self._bridge.send_signal(
                            {
                                "type": "futures_breakout",
                                "symbol": symbol,
                                "interval": "1m",
                                "message": text,
                            }
                        )
                        await self._sender.send_to_role("extreme", symbol, "futures", text)
                        logger.info("Breakout alert sent: %s", symbol)
                except Exception as exc:
                    logger.warning("Breakout error %s: %s", symbol, exc)
            await asyncio.sleep(self._config.futures_breakout_seconds)




