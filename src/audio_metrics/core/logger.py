"""
Logger Module
=============
Structured logging using structlog.
"""

import sys
from pathlib import Path
from typing import Optional

import structlog


def setup_logging(
    level: str = "INFO",
    log_file: Optional[Path] = None,
    json_output: bool = False,
) -> None:
    """
    Configure structured logging.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR)
        log_file: Optional file path for log output
        json_output: Whether to output JSON format
    """
    processors = [
        structlog.stdlib.add_log_level,
        structlog.processors.TimeStamper(fmt="iso"),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.format_exc_info,
    ]

    if json_output:
        processors.append(structlog.processors.JSONRenderer())
    else:
        processors.append(structlog.dev.ConsoleRenderer())

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.PrintLoggerFactory(),
        cache_logger_on_first_use=True,
    )

    # Set root logger level
    import logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, level.upper()))
        logging.getLogger().addHandler(file_handler)


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger instance.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Configured structlog logger
    """
    return structlog.get_logger(name)
