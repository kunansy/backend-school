#!/usr/bin/env python3
import logging
import os

from environs import Env
from pydantic import ValidationError
from sanic import Sanic, response
from sanic.exceptions import ServerError, abort
from sanic.log import error_logger
from sanic.request import Request
from uvloop.loop import Loop

import db_api
import logging_config
from model import CourierModel, validation_error, OrderModel, CompleteModel


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

    added_couriers = {
        "couriers": [
            courier.dict(include={'id'})
            for courier in couriers
        ]
    }
    return response.json(added_couriers, status=201)


@app.patch('/couriers/<courier_id>')
async def update_courier(request: Request,
                         courier_id: int) -> response.HTTPResponse:
    courier: CourierModel = await db_api.get_courier(courier_id)

    if courier is None:
        error_logger.error(f"Courier ({courier_id}) not found")
        abort(400)

    if invalid_fields := is_json_patching_courier_valid(request.json):
        error_logger.error(f"Only {PATCHABLE_FIELDS} might be "
                           f"updated, but {invalid_fields} found")
        abort(400)

    try:
        courier_data = {**courier.dict(), **request.json}
        updated_courier = CourierModel(**courier_data)
    except ValidationError as e:
        error_logger.error(e.json(indent=4))
        abort(400)

    await db_api.update_courier(updated_courier)

    return response.json(updated_courier.json())


@app.get('/couriers/<courier_id>')
async def get_courier(request: Request, courier_id) -> response.HTTPResponse:
    pass


@app.post('/orders')
async def add_orders(request: Request) -> response.HTTPResponse:
    orders, invalid_orders_id = [], []
    for order in request.json['data']:
        try:
            order = OrderModel(**order)
        except ValidationError as e:
            invalid_orders_id += [order.get('id', -1)]
            error_logger.error(e.json(indent=4))
        else:
            orders += [order]

    if invalid_orders_id:
        error_logger.error("Request rejected, it contains invalid "
                           f"orders ({len(invalid_orders_id)})")
        context = validation_error('orders', invalid_orders_id)
        return response.json(context, status=400)

    await db_api.add_orders(orders)

    added_orders = {
        "orders": [
            order.dict(include={'id'})
            for order in orders
        ]
    }
    return response.json(added_orders, status=201)


@app.post('/orders/assign')
async def assign(request: Request) -> response.HTTPResponse:
    courier_id = request.json.get('courier_id', -1)

    if (courier := db_api.get_courier(courier_id)) is None:
        error_logger.error(f"Courier with {courier_id=} not found")
        abort(400)

    assigned_orders = await db_api.assign_orders(courier)
    return response.json(assigned_orders)


@app.post('/orders/complete')
async def complete(request: Request) -> response.HTTPResponse:
    try:
        complete = CompleteModel(**request.json)
    except ValidationError as e:
        error_logger.error(f"Invalid complete request\n{e.json(indent=4)}")
        abort(400)

    if (courier := await db_api.get_courier(complete.courier_id)) is None:
        error_logger.error(f"Courier with {complete.courier_id} not found")
        abort(400)
    if (order := await db_api.get_order(complete.order_id)) is None:
        error_logger.error(f"Order with {complete.order_id} not found")
        abort(400)

    if (assign_info := await db_api.assign_info(order.order_id)) is None:
        error_logger.error(f"Order {order.order_id} was not assigned")
        abort(400)

    if (assigned_courier := assign_info.courier.courier_id) != courier.courier_id:
        error_logger.error(
            f"{order.order_id=} assigned to {assigned_courier.courier_id} "
            f"courier, but {courier.courier_id} found"
        )
        abort(400)

    await db_api.complete_order(complete)

    return response.json(complete.dict(include={'courier_id'}))


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
