import os
import sys

from environs import Env


env = Env()
env.read_env()

BASE_MESSAGE_FORMAT = "[%(asctime)s] [%(name)s:%(levelname)s] [%(module)s:%(funcName)s():%(process)d]"
DATE_FORMAT = "%d-%m-%Y %H:%M:%S"

FILE_LOGGING = 'INFO' if env.bool('FILE_LOGGING') else 'ERROR'
LOG_FOLDER = env.path('LOG_FOLDER')

try:
    os.makedirs(LOG_FOLDER, exist_ok=True)
except PermissionError as e:
    pass

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
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
            "stream": sys.stderr,
            "level": "DEBUG"
        },
        "internalFile": {
            "class": "logging.FileHandler",
            "formatter": "simple",
            "filename": LOG_FOLDER / "sweets_shop.log",
            "level": FILE_LOGGING
        },
        "errorFile": {
            "class": "logging.FileHandler",
            "formatter": "simple",
            "filename": LOG_FOLDER / "sweets_shop_error.log",
            "level": FILE_LOGGING
        },
        "accessStream": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "level": "DEBUG"
        },
        "accessFile": {
            "class": "logging.FileHandler",
            "formatter": "access",
            "filename": LOG_FOLDER / "sweets_shop_access.log",
            "level": FILE_LOGGING
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
            "level": "ERROR",
            "handlers": ["errorFile"]
        }
    }
}
