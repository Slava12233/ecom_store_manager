"""
Logging configuration for the application.
"""
import logging
import sys
from src.core.config import settings

def setup_logger() -> logging.Logger:
    """
    Configure and return the application logger.
    """
    logger = logging.getLogger("ecom_store_manager")
    logger.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Create console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setLevel(getattr(logging, settings.LOG_LEVEL.upper()))

    # Create formatter
    formatter = logging.Formatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    handler.setFormatter(formatter)

    # Add handler to logger
    logger.addHandler(handler)

    return logger

logger = setup_logger() 