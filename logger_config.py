"""Centralized logging configuration for the exam generator."""

import logging
import os
import sys
from typing import Optional

def setup_logger(name: Optional[str] = None) -> logging.Logger:
    """
    Configure and return a logger.

    In CI/CD environments (CI or GITHUB_ACTIONS env vars), only ERROR level is shown.
    Otherwise, INFO and above are displayed.
    """
    logger = logging.getLogger(name or __name__)

    # Only configure if not already configured
    if not logger.handlers:
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter('%(levelname)s: %(message)s')
        handler.setFormatter(formatter)
        logger.addHandler(handler)

        # Set level based on environment
        if os.getenv('CI') or os.getenv('GITHUB_ACTIONS'):
            logger.setLevel(logging.ERROR)
        else:
            logger.setLevel(logging.INFO)

    return logger
