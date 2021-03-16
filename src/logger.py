import sys


LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "simple": {
            "format": "[%(asctime)s] [%(name)s:%(levelname)s] [%(module)s:%(funcName)s():%(process)d] %(message)s ",
            "datefmt": "%d-%m-%Y %H:%M:%S"
        },
        "access": {
            "format": "[%(asctime)s] [%(name)s:%(levelname)s] [%(module)s:%(funcName)s():%(process)d] %(request)s, status: %(status)s, size: %(byte)sb",
            "datefmt": "%d-%m-%Y %H:%M:%S"
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
            "filename": "log/sanic.log",
            "level": "ERROR"
        },
        "errorFile": {
            "class": "logging.FileHandler",
            "formatter": "simple",
            "filename": "log/sanic-error.log",
            "level": "ERROR"
        },
        "accessStream": {
            "class": "logging.StreamHandler",
            "formatter": "access",
            "level": "DEBUG"
        },
        "accessFile": {
            "class": "logging.FileHandler",
            "formatter": "access",
            "filename": "log/sanic-access.log",
            "level": "ERROR"
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
