"""
Structured logging configuration for Vayu-Drishti.

Uses structlog for structured, JSON-formatted logs that can be
ingested by ELK, Datadog, or any log aggregation platform.
Supports correlation IDs for distributed tracing across services.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

import structlog
from structlog.contextvars import merge_contextvars
from structlog.dev import ConsoleRenderer
from structlog.processors import JSONRenderer, TimeStamper, add_log_level

from src.config import config


def setup_logging() -> None:
    """Configure structured logging for the entire application.

    In development, uses colorful console output with timestamps.
    In production, outputs JSON for log aggregation systems.
    """
    common_processors: list[Any] = [
        merge_contextvars,
        add_log_level,
        TimeStamper(fmt="iso", utc=True),
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
        structlog.processors.UnicodeDecoder(),
    ]

    if config.app_env == "production":
        renderer: Any = JSONRenderer()
    else:
        renderer = ConsoleRenderer(colors=True)

    structlog.configure(
        processors=common_processors + [renderer],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Wire structlog into standard logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, config.app_log_level.upper(), logging.INFO),
    )

    root_logger = structlog.get_logger()
    root_logger.info("Logging configured", environment=config.app_env, level=config.app_log_level)


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    """Get a structured logger instance with optional module name."""
    return structlog.get_logger(name or __name__)
