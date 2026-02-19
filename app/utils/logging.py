import logging
import os
from logging.handlers import TimedRotatingFileHandler
from typing import Optional


def setup_logging(log_level: str, log_dir: Optional[str], retention_days: int) -> None:
    """Configure console + daily rotating file logs."""
    level = getattr(logging, (log_level or "INFO").upper(), logging.INFO)

    root = logging.getLogger()
    root.setLevel(level)

    for handler in list(root.handlers):
        root.removeHandler(handler)

    formatter = logging.Formatter("%(asctime)s [%(levelname)s] %(name)s: %(message)s")

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(formatter)
    root.addHandler(console_handler)

    if log_dir:
        os.makedirs(log_dir, exist_ok=True)
        file_path = os.path.join(log_dir, "bot.log")
        file_handler = TimedRotatingFileHandler(
            filename=file_path,
            when="midnight",
            backupCount=max(retention_days, 14),
            encoding="utf-8",
        )
        file_handler.setFormatter(formatter)
        root.addHandler(file_handler)
