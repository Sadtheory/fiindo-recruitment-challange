# src/utils/logger.py

import logging
import sys
from pathlib import Path


def setup_logger(name: str = __name__) -> logging.Logger:
    """Set up and return a logger instance."""

    # Log directory
    log_dir = Path("logs")
    log_dir.mkdir(exist_ok=True)

    # Logger erstellen
    logger = logging.getLogger(name)

    if not logger.handlers:
        logger.setLevel(logging.INFO)

        # Formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
        )

        # Console Handler
        console_handler = logging.StreamHandler(sys.stdout)
        console_handler.setFormatter(formatter)
        logger.addHandler(console_handler)

        # File Handler
        file_handler = logging.FileHandler(log_dir / "fiindo_challenge.log")
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)

    return logger