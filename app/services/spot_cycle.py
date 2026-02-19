"""Spot signal cycle runner."""

from __future__ import annotations

import asyncio
import logging

from app.config import Config
from app.db.database import Database
from app.services.analysis import analyze_coin
from app.services.mexc_api import MexcClient
from app.services.optional_bridge import TraderBridge
from app.services.signal_formatter import format_spot_signal, naive_entry_tp_sl
from app.services.signal_sender import SignalSender

logger = logging.getLogger("spot_cycle")


class SpotSignalCycle:
    """Periodic spot analysis + signal sender."""

    def __init__(
        self,
        config: Config,
        db: Database,
        mexc: MexcClient,
        sender: SignalSender,
        bridge: TraderBridge,
    ) -> None:
        self._config = config
        self._db = db
        self._mexc = mexc
        self._sender = sender
        self._bridge = bridge

    async def run_once(self) -> None:
        for coin in self._config.coins_list:
            try:
                res = await analyze_coin(coin, self._config.timeframe, self._mexc, self._db)
                entry, tps, sl = naive_entry_tp_sl(res.last_close)
                msg = format_spot_signal(res, entry, tps, sl)

                await self._bridge.send_signal(
                    {
                        "type": "spot",
                        "symbol": coin,
                        "interval": self._config.timeframe,
                        "message": msg,
                    }
                )

                for role in ("free", "vip", "extreme"):
                    await self._sender.send_to_role(role, coin, "spot", msg)

                logger.info("Spot signal sent: %s", coin)
                await asyncio.sleep(0.5)
            except Exception as exc:
                logger.exception("Spot cycle error for %s: %s", coin, exc)

    async def run_loop(self) -> None:
        while True:
            logger.info("Spot cycle tick")
            await self.run_once()
            await asyncio.sleep(self._config.spot_cycle_seconds)
