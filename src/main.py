#!/usr/bin/env python3
import logging
import os

from environs import Env
from sanic import Sanic
from sanic.request import Request

import logger


app = Sanic(__name__, log_config=logger.LOGGING_CONFIG)
env = Env()
env.read_env()


@app.route("/")
async def home(request: Request):
    return json({"Method": request.method})


if __name__ == "__main__":
    # use all server power but don't destroy developer's
    # computer, means use just one worker on his machine
    workers = 2 * os.cpu_count() * (not env.bool('DEBUG')) + 1
    logger_level = 'DEBUG' if env.bool('DEBUG') else 'INFO'

    logging.getLogger('sanic.root').setLevel(logger_level)
    logging.getLogger('sanic.access').setLevel(logger_level)

    params = {
        'host': env('HOST'),
        'port': env.int('PORT'),
        'debug': env.bool('DEBUG'),
        'access_log': env.bool('ACCESS_LOG'),
        'workers': workers
    }
    app.run(**params)
