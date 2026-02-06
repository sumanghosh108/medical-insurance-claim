"""Logging Module - JSON and File Logging."""

import logging
import os
import sys
from logging.handlers import RotatingFileHandler
from typing import Optional
from pythonjsonlogger import jsonlogger


def setup_logging(
    name: str,
    level: Optional[str] = None,
    log_file: Optional[str] = None,
    use_json: bool = False,
) -> logging.Logger:
    """Setup logger with handlers."""
    level_str = (level or os.getenv("LOG_LEVEL", "INFO")).upper()
    log_level = getattr(logging, level_str, logging.INFO)
    
    logger = logging.getLogger(name)
    logger.setLevel(log_level)
    
    if logger.handlers:
        logger.handlers.clear()
    
    if use_json:
        formatter = jsonlogger.JsonFormatter(
            fmt="%(timestamp)s %(level)s %(name)s %(message)s"
        )
    else:
        formatter = logging.Formatter(
            fmt="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S",
        )
    
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(log_level)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    if log_file:
        os.makedirs(os.path.dirname(log_file) or ".", exist_ok=True)
        file_handler = RotatingFileHandler(
            log_file,
            maxBytes=10 * 1024 * 1024,
            backupCount=10,
        )
        file_handler.setLevel(log_level)
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    logger.propagate = False
    return logger


def get_logger(
    name: str,
    log_file: Optional[str] = None,
    use_json: bool = False,
) -> logging.Logger:
    """Get or create logger."""
    logger = logging.getLogger(name)
    if not logger.handlers:
        setup_logging(name, None, log_file, use_json)
    return logger


def configure_module_logging(
    module_name: str,
    log_dir: str = "./logs",
    use_json: bool = True,
) -> logging.Logger:
    """Configure module-specific logging."""
    log_file = os.path.join(log_dir, f"{module_name}.log")
    return setup_logging(module_name, None, log_file, use_json)


def log_performance(logger: logging.Logger, function_name: str, duration: float):
    """Log function performance."""
    if duration > 1.0:
        logger.warning(f"{function_name} took {duration:.2f}s")
    else:
        logger.debug(f"{function_name} took {duration:.3f}s")


def log_error_with_context(
    logger: logging.Logger,
    message: str,
    exception: Exception,
    context: Optional[dict] = None,
):
    """Log error with context."""
    extra = ""
    if context:
        extra = " | " + " | ".join(f"{k}={v}" for k, v in context.items())
    logger.error(f"{message}{extra}", exc_info=exception)







# import logging
# import logging.config
# import os
# from datetime import datetime

# LOG_DIR="logs"
# os.makedirs(LOG_DIR,exist_ok=True)

# # Create unique log file per run
# LOG_FILE=os.path.join(LOG_DIR, f"run_{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log")

# LOGGING_CONFIG = {
#     "version": 1,
#     "disable_existing_loggers": False,

#     "formatters": {
#         "default": {
#             "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
#         }
#     },

#     "handlers": {
#         "file": {
#             "class": "logging.FileHandler",
#             "filename": LOG_FILE,
#             "formatter": "default",
#             "level": "INFO",
#         },
#         "console": {
#             "class": "logging.StreamHandler",
#             "formatter": "default",
#             "level": "INFO",
#         }
#     },

#     "root": {
#         "handlers": ["file", "console"],
#         "level": "INFO",
#     }
# }

# # Initialize logging ONCE
# def setup_logging():
#     """
#     Must be called ONCE at application startup.
#     Safe with FastAPI + Uvicorn reload.
#     """
#     logging.config.dictConfig(LOGGING_CONFIG)


# # Logger accessor
# def get_logger(name: str) -> logging.Logger:
#     return logging.getLogger(name)