"""
Logging configuration for Healthcare Assistant Prototype.
Provides centralized logging setup for all modules.
"""

import logging
import logging.config
import os
from pathlib import Path
from typing import Optional

# Get the project root directory
PROJECT_ROOT = Path(__file__).parent.parent
LOG_DIR = PROJECT_ROOT / "logs"

# Create logs directory if it doesn't exist
LOG_DIR.mkdir(exist_ok=True)


# Logging configuration dictionary
LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "detailed": {
            "format": "%(asctime)s - %(name)s - %(levelname)s - [%(filename)s:%(lineno)d] - %(funcName)s() - %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
        "simple": {
            "format": "%(levelname)s - %(message)s",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "level": "INFO",
            "formatter": "standard",
            "stream": "ext://sys.stdout",
        },
        "console_debug": {
            "class": "logging.StreamHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "stream": "ext://sys.stdout",
        },
        "file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "DEBUG",
            "formatter": "detailed",
            "filename": str(LOG_DIR / "app.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
        "error_file": {
            "class": "logging.handlers.RotatingFileHandler",
            "level": "ERROR",
            "formatter": "detailed",
            "filename": str(LOG_DIR / "error.log"),
            "maxBytes": 10485760,  # 10MB
            "backupCount": 5,
        },
    },
    "loggers": {
        # Root logger
        "": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
        },
        # Module-specific loggers
        "src.agents": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        "src.api": {
            "level": "INFO",
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        "src.ingestion": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        "src.storage": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        "src.tools": {
            "level": "DEBUG",
            "handlers": ["console", "file", "error_file"],
            "propagate": False,
        },
        # Third-party loggers - reduce noise
        "langchain": {
            "level": "INFO",
            "handlers": ["console", "file"],
            "propagate": False,
        },
        "chromadb": {
            "level": "WARNING",
            "handlers": ["file"],
            "propagate": False,
        },
    },
}


def setup_logging(
    debug: bool = False,
    log_level: Optional[str] = None,
) -> logging.Logger:
    """
    Configure logging for the application.

    Args:
        debug: If True, use DEBUG level for console output
        log_level: Override default log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)

    Returns:
        Configured logger instance
    """
    config = LOGGING_CONFIG.copy()

    # Adjust console handler level if debug mode is enabled
    if debug:
        config["handlers"]["console"]["level"] = "DEBUG"
        config["handlers"]["console"]["formatter"] = "detailed"

    # Override log level if specified
    if log_level:
        config["loggers"][""]["level"] = log_level.upper()

    # Apply configuration
    logging.config.dictConfig(config)

    return logging.getLogger(__name__)


def get_logger(name: str) -> logging.Logger:
    """
    Get a logger instance for a specific module.

    Args:
        name: Logger name (typically __name__)

    Returns:
        Logger instance
    """
    return logging.getLogger(name)


# Initialize logging on import if not already configured
if not logging.getLogger().handlers:
    setup_logging()
