import logging
from enum import Enum

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class LogLevel(Enum):
    """Enum for log levels."""

    INFO = "info"
    ERROR = "error"
    DEBUG = "debug"
    WARNING = "warning"


def log_to_aws(level=LogLevel.INFO, message="") -> None:
    """Logs to AWS CloudWatch."""

    if level == LogLevel.INFO:
        logger.info(message)
    elif level == LogLevel.ERROR:
        logger.error(message)
    elif level == LogLevel.DEBUG:
        logger.debug(message)
    elif level == LogLevel.WARNING:
        logger.warning(message)
    else:
        logger.info(message)
