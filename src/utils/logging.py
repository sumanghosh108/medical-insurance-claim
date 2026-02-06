import logging
import logging.config
import os
from datetime import datetime

LOG_DIR="logs"
os.makedirs(LOG_DIR,exist_ok=True)

# Create unique log file per run
LOG_FILE=os.path.join(LOG_DIR, f"run_{datetime.now().strftime('%m_%d_%Y_%H_%M_%S')}.log")

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,

    "formatters": {
        "default": {
            "format": "[%(asctime)s] [%(levelname)s] [%(name)s] %(message)s",
        }
    },

    "handlers": {
        "file": {
            "class": "logging.FileHandler",
            "filename": LOG_FILE,
            "formatter": "default",
            "level": "INFO",
        },
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "default",
            "level": "INFO",
        }
    },

    "root": {
        "handlers": ["file", "console"],
        "level": "INFO",
    }
}

# Initialize logging ONCE
def setup_logging():
    """
    Must be called ONCE at application startup.
    Safe with FastAPI + Uvicorn reload.
    """
    logging.config.dictConfig(LOGGING_CONFIG)


# Logger accessor
def get_logger(name: str) -> logging.Logger:
    return logging.getLogger(name)