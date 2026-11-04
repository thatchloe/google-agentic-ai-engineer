"""
Logging Configuration for Legal Intelligence AI System
======================================================
"""

import logging
import sys
from contextvars import ContextVar
from pathlib import Path

# Set once per report so every log line from that run can be traced together.
# asyncio.to_thread copies this into worker threads.
run_id_var: ContextVar[str] = ContextVar("run_id", default="-")


class RunIdFilter(logging.Filter):
    """Add the current run ID to each log record."""

    def filter(self, record: logging.LogRecord) -> bool:
        record.run_id = run_id_var.get()
        return True


def setup_logger(name: str = "legal-intelligence", level: str = "INFO") -> logging.Logger:
    """
    Set up structured logging for the application.

    Args:
        name: Logger name
        level: Logging level (DEBUG, INFO, WARNING, ERROR)

    Returns:
        Configured logger instance
    """
    # Create logger
    logger = logging.getLogger(name)
    logger.setLevel(getattr(logging, level.upper()))

    # Remove existing handlers to avoid duplicates
    logger.handlers.clear()

    # Create console handler with formatting
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, level.upper()))

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - run=%(run_id)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    console_handler.setFormatter(formatter)
    console_handler.addFilter(RunIdFilter())

    # Add handler to logger
    logger.addHandler(console_handler)

    return logger