#!/usr/bin/env python3
import logging
import os

from environs import Env
from pydantic import ValidationError
from sanic import Sanic, response
from sanic.log import error_logger
from sanic.request import Request
from uvloop.loop import Loop

import db_api
import logging_config
from model import CourierModel, validation_error


PATCHABLE_FIELDS = [
    'courier_type', 'regions', 'working_hours'
]


def is_json_patching_courier_valid(json_dict: dict) -> list[str]:
    """
    Check whether the request to patch a courier valid,
    means there are only particular fields and nothing else.

    :param json_dict: json to validate.
    :return: list of invalid fields if there are.
    """
    # TODO: make copy or not?
    for field in PATCHABLE_FIELDS:
        json_dict.pop(field)

    return list(json_dict.keys())


app = Sanic(__name__, log_config=logging_config.LOGGING_CONFIG)
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


@app.post('/couriers')
async def add_couriers(request: Request) -> response.HTTPResponse:
    couriers, invalid_couriers_id = [], []
    for courier in request.json['data']:
        try:
            courier = CourierModel(**courier)
        except ValidationError as e:
            invalid_couriers_id += [courier.get('id', -1)]
            error_logger.error(e.json(indent=4))
        else:
            couriers += [courier]

    if invalid_couriers_id:
        error_logger.error("Request rejected, it contains invalid "
                           f"couriers ({len(invalid_couriers_id)})")
        context = validation_error('couriers', invalid_couriers_id)
        return response.json(context, status=400)

    await db_api.add_couriers(couriers)

    return response.json(couriers, status=201)


@app.patch('/couriers/<courier_id>')
async def update_courier(request: Request,
                         courier_id: int) -> response.HTTPResponse:
    courier = await db_api.get_courier(courier_id)

    if invalid_fields := is_json_patching_courier_valid(request.json):
        error_logger.error(f"Only {PATCHABLE_FIELDS} might be "
                           f"updated, but {invalid_fields} found")
        return response.HTTPResponse(400)

    try:
        updated_courier = CourierModel(**courier.json(), **request.json)
    except ValidationError as e:
        error_logger.error(e.json(indent=4))
        return response.HTTPResponse(status=400)

    await db_api.update_courier(updated_courier)

    return response.json(updated_courier.json())


@app.get('/couriers/<courier_id>')
async def get_courier(request: Request, courier_id) -> response.HTTPResponse:
    pass


@app.post('/orders')
async def add_orders(request: Request) -> response.HTTPResponse:
    pass


@app.post('/orders/assign')
async def couriers(request: Request) -> response.HTTPResponse:
    pass


@app.post('/orders/complete')
async def couriers(request: Request) -> response.HTTPResponse:
    pass


@app.exception(ServerError, Exception)
async def error_handler(request: Request,
                        exception: Exception) -> response.HTTPResponse:
    try:
        error_json = exception.json()
    except AttributeError:
        error_json = ''

    context = {
        "ok": False,
        "wrong_request": request.json,
        "error": {
            "type": exception.__class__.__name__,
            "text": str(exception),
            "args": exception.args,
            "json": error_json
        }
    }
    return response.json(context, indent=4)


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
