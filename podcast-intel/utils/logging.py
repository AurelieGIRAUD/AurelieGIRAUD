"""
Logging setup utilities.

Configures logging for the application following "Observable by Default" principle.
"""

import logging
import sys
from pathlib import Path
from datetime import datetime


def setup_logging(log_level: str = "INFO", logs_directory: str = "logs") -> None:
    """
    Configure logging for the application.

    Design principle: "Observable by Default"
    - Console output for interactive use
    - File logging for audit trail
    - Structured, readable format

    Args:
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        logs_directory: Directory for log files
    """
    # Create logs directory
    log_dir = Path(logs_directory)
    log_dir.mkdir(parents=True, exist_ok=True)

    # Log file with timestamp
    log_file = log_dir / f"podcast_intel_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )

    # Console handler (stdout)
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    console_handler.setFormatter(formatter)

    # File handler
    file_handler = logging.FileHandler(log_file)
    file_handler.setLevel(logging.DEBUG)  # Log everything to file
    file_handler.setFormatter(formatter)

    # Root logger configuration
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)  # Capture everything
    root_logger.handlers = []  # Clear existing handlers
    root_logger.addHandler(console_handler)
    root_logger.addHandler(file_handler)

    # Silence noisy libraries
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('feedparser').setLevel(logging.WARNING)

    logging.info(f"Logging configured - Level: {log_level}, Log file: {log_file}")
