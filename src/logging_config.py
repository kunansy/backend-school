import logging
import os
import sys
from typing import List

from environs import Env


env = Env()
env.read_env()

BASE_MESSAGE_FORMAT = "[%(asctime)s] [%(name)s:%(levelname)s] " \
                      "[%(module)s:%(funcName)s():%(process)d]"
DATE_FORMAT = "%d-%m-%Y %H:%M:%S"

LOG_FOLDER = env.path('LOG_FOLDER')
DEBUG = env.bool('DEBUG')

try:
    os.makedirs(LOG_FOLDER, exist_ok=True)
except PermissionError as e:
    pass


class LevelFilter(logging.Filter):
    def __init__(self,
                 levels: List[int] = None) -> None:
        self._levels = levels or []
        super().__init__(self.__class__.__name__)

    def filter(self,
               record: logging.LogRecord) -> bool:
        return record.levelno in self._levels


class DebugFilter(logging.Filter):
    """ The filter is designed to skip logging to file
    if DEBUG is True and skip logging to stream otherwise. """
    def __init__(self,
                 debug: bool) -> None:
        self._debug = debug
        super().__init__(self.__class__.__name__)

    def filter(self,
               record: logging.LogRecord) -> bool:
        return self._debug


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "filters": {
        "internalFilter": {
            "()": LevelFilter,
            "levels": [0, 10, 20]
        },
        "errorFilter": {
            "()": LevelFilter,
            "levels": [30, 40, 50]
        },
        "debugFileFilter": {
            "()": DebugFilter,
            "debug": not DEBUG
        },
        "debugStreamFilter": {
            "()": DebugFilter,
            "debug": DEBUG
        }
    },
    "formatters": {
        "simple": {
            "format": f"{BASE_MESSAGE_FORMAT} %(message)s",
            "datefmt": DATE_FORMAT
        },
        "access": {
            "format": f"{BASE_MESSAGE_FORMAT} %(request)s, status: %(status)s, size: %(byte)sb",
            "datefmt": DATE_FORMAT
        }
    },
    "handlers": {
        "internalStream": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "filters": ["internalFilter", "debugStreamFilter"],
            "stream": sys.stderr,
            "level": "DEBUG"
        },
        "internalFile": {
            "class": "logging.FileHandler",
            "formatter": "simple",
            "filters": ["internalFilter", "debugFileFilter"],
            "filename": LOG_FOLDER / "sweets_shop.log",
            "level": "INFO"
        },
        "errorStream": {
            "class": "logging.StreamHandler",
            "formatter": "simple",
            "filters": ["errorFilter", "debugStreamFilter"],
            "stream": sys.stderr,
            "level": "WARNING"
        },
        "errorFile": {
            "class": "logging.FileHandler",
            "formatter": "simple",
            "filters": ["errorFilter", "debugFileFilter"],
            "filename": LOG_FOLDER / "sweets_shop_error.log",
            "level": "WARNING"
        },
        "accessStream": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "filters": ["internalFilter", "debugStreamFilter"],
            "level": "DEBUG"
        },
        "accessFile": {
            "class": "logging.FileHandler",
            "formatter": "access",
            "filters": ["internalFilter", "debugFileFilter"],
            "filename": LOG_FOLDER / "sweets_shop_access.log",
            "level": "INFO"
        }
    },
    "loggers": {
        "sanic.root": {
            "level": "DEBUG",
            "handlers": ["internalStream", "internalFile"]
        },
        "sanic.access": {
            "level": "DEBUG",
            "handlers": ["accessStream", "accessFile"]
        },
        "sanic.error": {
            "level": "WARNING",
            "handlers": ["errorStream", "errorFile"]
        }
    }
}
