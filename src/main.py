#!/usr/bin/env python3

import argparse

from environs import Env
from sanic import Sanic
from sanic.request import Request
from sanic.response import json


app = Sanic(__name__)
env = Env()
env.read_env()


@app.route("/")
async def home(request: Request):
    return json({"Method": request.method})


if __name__ == "__main__":
    parser = argparse.ArgumentParser(
        description=""
    )
    parser.add_argument(
        '--debug',
        help="If true run sanic in debug mode",
        action="store_true",
        default=False,
        dest="debug"
    )
    args = parser.parse_args()

    params = {
        'host': env('HOST'),
        'port': env.int('PORT'),
        'debug': env.bool('DEBUG'),
        'access_log': env.bool('ACCESS_LOG'),
        'workers': workers
    }
    app.run(**params)
