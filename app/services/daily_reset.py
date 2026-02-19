import asyncio
import logging

from app.config import Config
from app.db.database import Database
from app.utils.time import seconds_until_next_midnight

logger = logging.getLogger("daily_reset")


async def daily_reset_task(db: Database, config: Config) -> None:
    """Reset daily free limits at midnight (server local time)."""
    while True:
        # Sleep until the next midnight boundary (server local time).
        wait = seconds_until_next_midnight()
        await asyncio.sleep(wait)
        try:
            await db.reset_daily_limits()
            logger.info("Daily free limits reset to %s", config.default_free_limit)
        except Exception as exc:
            logger.warning("Daily reset failed: %s", exc)
