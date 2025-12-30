import logging


def configure_logging():
    """Configure logging consistent with existing defaults (no level change)."""
    logging.basicConfig(level=logging.INFO)
    return logging.getLogger("dl")

__all__ = ["configure_logging"]
