"""
Application logging configuration.

Features
--------
- Structlog integration
- Console logging
- JSON-ready processors
- Bound loggers
- Production-friendly defaults
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog


def configure_logging() -> None:
    """
    Configure Python logging and structlog.
    """

    logging.basicConfig(
        level=logging.INFO,
        format="%(message)s",
        stream=sys.stdout,
    )

    processors = [
        structlog.contextvars.merge_contextvars,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
        structlog.dev.ConsoleRenderer(),
    ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


configure_logging()


def get_logger(name: str | None = None) -> Any:
    """
    Return configured structlog logger.

    Parameters
    ----------
    name:
        Logger name.

    Returns
    -------
    structlog.BoundLogger
    """

    if name:
        return structlog.get_logger(name)

    return structlog.get_logger()