"""Centralized logging infrastructure with test context correlation.

This module provides structured logging that integrates with test execution,
capturing correlation IDs and contextual information for debugging.
"""

from __future__ import annotations

import logging
import sys
from typing import Any

from src.services.test_context import TestContext


def configure_logging(level: str = "INFO") -> None:
    """Configure root logger with structured format.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL).
    """
    logging.basicConfig(
        level=getattr(logging, level.upper()),
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S",
        stream=sys.stdout,
    )


def get_logger(name: str, context: TestContext | None = None) -> logging.Logger:
    """Get a logger with optional test context binding.

    Args:
        name: Logger name (typically __name__ of calling module).
        context: Optional test context for correlation ID injection.

    Returns:
        Configured logger instance.

    Examples:
        >>> # Basic logger
        >>> logger = get_logger(__name__)
        >>> logger.info("Test started")

        >>> # Logger with test context
        >>> logger = get_logger(__name__, test_context)
        >>> logger.info("API call", extra={"endpoint": "/settlements"})
    """
    logger = logging.getLogger(name)

    if context:
        # Add context filter to inject correlation ID
        logger.addFilter(ContextFilter(context))

    return logger


class ContextFilter(logging.Filter):
    """Logging filter that adds test context information to log records."""

    def __init__(self, context: TestContext) -> None:
        super().__init__()
        self.context = context

    def filter(self, record: logging.LogRecord) -> bool:
        """Add context fields to log record."""
        record.correlation_id = self.context.correlation_id  # type: ignore[attr-defined]
        record.run_id = self.context.run_id  # type: ignore[attr-defined]
        return True


def log_api_call(
    logger: logging.Logger,
    method: str,
    url: str,
    status_code: int | None = None,
    duration_ms: float | None = None,
    **kwargs: Any,
) -> None:
    """Log API call with structured data.

    Args:
        logger: Logger instance.
        method: HTTP method (GET, POST, etc.).
        url: Request URL.
        status_code: Response status code (if available).
        duration_ms: Request duration in milliseconds.
        **kwargs: Additional context (headers, payload, error, etc.).
    """
    extra = {
        "method": method,
        "url": url,
        "status_code": status_code,
        "duration_ms": duration_ms,
        **kwargs,
    }

    if status_code and status_code >= 400:
        logger.error(f"API call failed: {method} {url}", extra=extra)
    else:
        logger.info(f"API call: {method} {url}", extra=extra)


def log_test_step(
    logger: logging.Logger,
    step: str,
    **kwargs: Any,
) -> None:
    """Log test execution step with context.

    Args:
        logger: Logger instance.
        step: Description of test step.
        **kwargs: Additional context.
    """
    logger.info(f"Test step: {step}", extra=kwargs)
