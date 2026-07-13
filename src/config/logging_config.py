# src/config/logging_config.py — Loguru setup (Member 4)
from __future__ import annotations
import sys
from pathlib import Path
from loguru import logger
from src.config.settings import settings


def setup_logging(log_file: str | None = None) -> None:
    logger.remove()
    logger.add(sys.stderr, level=settings.log_level,
               format="<green>{time:HH:mm:ss}</green> | <level>{level:<7}</level> | "
                      "<cyan>{name}</cyan> - {message}")
    if log_file:
        Path(log_file).parent.mkdir(parents=True, exist_ok=True)
        logger.add(log_file, level="DEBUG", rotation="10 MB", retention=5)