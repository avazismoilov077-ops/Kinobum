import logging
import os
from logging.handlers import RotatingFileHandler
from datetime import datetime

os.makedirs("bot/logs", exist_ok=True)

LOG_FILE = f"bot/logs/bot_{datetime.now().strftime('%Y-%m-%d')}.log"


def setup_logger() -> logging.Logger:
    logger = logging.getLogger("kino_bot")
    logger.setLevel(logging.INFO)

    formatter = logging.Formatter(
        "%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console handler
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_handler.setFormatter(formatter)

    # File handler (10MB, max 5 fayl)
    file_handler = RotatingFileHandler(
        LOG_FILE, maxBytes=10 * 1024 * 1024, backupCount=5, encoding="utf-8"
    )
    file_handler.setLevel(logging.INFO)
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)

    return logger


logger = setup_logger()
