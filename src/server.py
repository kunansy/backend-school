#!/usr/bin/env python3
import logging
import os

from environs import Env
from pydantic import ValidationError
from sanic import Sanic, response
from sanic.request import Request
from uvloop.loop import Loop

import logger
from src.model import CourierModel, validation_error

app = Sanic(__name__, log_config=logger.LOGGING_CONFIG)
env = Env()
env.read_env()


@app.listener('after_server_start')
async def create_db_connection(app: Sanic,
                               loop: Loop) -> None:
    pass


@app.listener('after_server_stop')
async def close_db_connection(app: Sanic,
                              loop: Loop) -> None:
    pass


@app.route('/couriers', methods=['POST'])
async def add_couriers(request: Request) -> response.HTTPResponse:
    couriers, invalid_couriers_id = [], []
    for courier in request.json['data']:
        try:
            courier = CourierModel(**courier)
        except ValidationError as e:
            invalid_couriers_id += [courier.get('id', -1)]
            # logger.error(e.json(indent=4))
        else:
            couriers += [courier]

    if invalid_couriers_id:
        # logger.error("Request rejected, it contains invalid "
        #              f"couriers ({len(invalid_couriers_id)})")
        context = validation_error('couriers', invalid_couriers_id)
        return response.json(context, status=400)

    # await db_api.add_couriers(couriers)
    return response.json(couriers, status=201)


@app.route('/couriers/<courier_id>', methods=['PATCH'])
async def update_courier(request: Request, courier_id) -> response.HTTPResponse:
    pass


@app.route('/couriers/<courier_id>', methods=['GET'])
async def get_courier(request: Request, courier_id) -> response.HTTPResponse:
    pass


@app.route('/orders', methods=['POST'])
async def add_orders(request: Request) -> response.HTTPResponse:
    pass


@app.route('/orders/assign', methods=['POST'])
async def couriers(request: Request) -> response.HTTPResponse:
    pass


@app.route('/orders/complete', methods=['POST'])
async def couriers(request: Request) -> response.HTTPResponse:
    pass


if __name__ == "__main__":
    debug = env.bool('DEBUG', False)

    # use all server power but don't destroy developer's
    # computer, means use just one worker on his machine
    workers = 2 * os.cpu_count() * (not debug) + 1
    logger_level = 'DEBUG' if debug else 'INFO'

    logging.getLogger('sanic.root').setLevel(logger_level)
    logging.getLogger('sanic.access').setLevel(logger_level)

    app.run(
        host=env('HOST'),
        port=env.int('PORT'),
        debug=debug,
        access_log=env.bool('ACCESS_LOG'),
        workers=workers,
        auto_reload=True
    )
