"""Application entrypoint for the crypto signal bot."""

from __future__ import annotations

import asyncio
import logging

from aiogram import Bot, Dispatcher

from app.config import load_config
from app.db.database import Database
from app.handlers import admin, user
from app.services.daily_reset import daily_reset_task
from app.services.futures_breakout import FuturesBreakoutWatcher
from app.services.mexc_api import MexcClient
from app.services.optional_bridge import TraderBridge
from app.services.signal_sender import SignalSender
from app.services.spot_cycle import SpotSignalCycle
from app.utils.logging import setup_logging

logger = logging.getLogger("main")


def _create_task(coro, name: str) -> asyncio.Task:
    """Create a named asyncio task for background services."""
    return asyncio.create_task(coro, name=name)


async def main() -> None:
    """Bootstrap config, services, and start the Telegram polling loop."""
    config = load_config()
    setup_logging(config.log_level, config.log_dir, config.log_retention_days)

    bot = Bot(token=config.bot_token, parse_mode="HTML")
    dp = Dispatcher()

    db = Database(config)
    await db.connect()
    await db.init_schema()

    mexc = MexcClient(config)
    await mexc.start()

    bridge = TraderBridge(config)
    await bridge.start()

    sender = SignalSender(bot, db, config)

    dp["db"] = db
    dp["config"] = config
    dp["sender"] = sender
    dp["mexc"] = mexc
    dp["bridge"] = bridge

    dp.include_router(user.router)
    dp.include_router(admin.router)

    # Start background services based on feature flags.
    bg_tasks = []
    if config.enable_spot_cycle:
        spot_cycle = SpotSignalCycle(config, db, mexc, sender, bridge)
        bg_tasks.append(_create_task(spot_cycle.run_loop(), "spot_cycle"))
    if config.enable_futures_breakout:
        breakout = FuturesBreakoutWatcher(config, mexc, sender, bridge)
        bg_tasks.append(_create_task(breakout.run_loop(), "breakout"))
    if config.enable_daily_reset:
        bg_tasks.append(_create_task(daily_reset_task(db, config), "daily_reset"))

    logger.info("Bot started. Polling...")
    try:
        await dp.start_polling(bot)
    finally:
        for task in bg_tasks:
            task.cancel()
        await asyncio.gather(*bg_tasks, return_exceptions=True)
        await bridge.close()
        await mexc.close()
        await bot.session.close()
        await db.close()


if __name__ == "__main__":
    asyncio.run(main())
