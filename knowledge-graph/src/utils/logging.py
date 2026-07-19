"""Structured logging for the knowledge graph service."""

from __future__ import annotations

import logging
import sys

import structlog


def get_logger(name: str | None = None) -> structlog.stdlib.BoundLogger:
    structlog.configure(
        processors=[
            structlog.contextvars.merge_contextvars,
            structlog.stdlib.add_log_level,
            structlog.dev.ConsoleRenderer(colors=True),
        ],
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )
    logging.basicConfig(format="%(message)s", stream=sys.stdout, level=logging.INFO)
    return structlog.get_logger(name or __name__)
