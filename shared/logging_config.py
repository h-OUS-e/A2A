"""
Centralized logging configuration for all A2A agents.
Provides consistent log formatting with timestamps, agent names, and context.
"""

import logging
import sys
from typing import Optional

# Log format with timestamp, level, logger name, and message
LOG_FORMAT = '%(asctime)s [%(levelname)s] [%(name)s] %(message)s'
DATE_FORMAT = '%Y-%m-%d %H:%M:%S'


def setup_logging(agent_name: Optional[str] = None, level: int = logging.INFO):
    """
    Configure logging for an agent or client.

    Args:
        agent_name: Name of the agent (e.g., "person_a", "person_b", "trigger_client")
        level: Logging level (default: INFO)
    """
    # Get or create logger
    logger = logging.getLogger(agent_name or "a2a")
    logger.setLevel(level)

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Console handler with formatting
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(level)
    formatter = logging.Formatter(LOG_FORMAT, datefmt=DATE_FORMAT)
    handler.setFormatter(formatter)
    logger.addHandler(handler)

    # Don't propagate to root logger to avoid duplicates
    logger.propagate = False

    return logger


def get_logger(name: str) -> logging.Logger:
    """Get a logger instance for a specific module."""
    return logging.getLogger(name)
