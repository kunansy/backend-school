#!/usr/bin/env python3

import argparse

from sanic import Sanic
from sanic.request import Request
from sanic.response import json

app = Sanic(__name__)


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

    app.run(host="0.0.0.0", port=8080, debug=args.debug)
