#!/usr/bin/env python3
import logging
import os
import sys
from typing import List

from environs import Env
from pydantic import ValidationError
from sanic import Sanic, response
from sanic.exceptions import ServerError, abort
from sanic.log import error_logger
from sanic.request import Request
from sanic_openapi import swagger_blueprint, doc


sys.path += [
    os.path.abspath('..'),
    os.path.abspath('.')
]


from src.db_api import Database
import src.logging_config as logging_config
from src.model import CourierModel, validation_error, OrderModel, CompleteModel


os.environ['PYTHONWARNINGS'] = 'ignore'

PATCHABLE_FIELDS = [
    'courier_type', 'regions', 'working_hours'
]


def is_json_patching_courier_valid(json_dict: dict) -> List[str]:
    """
    Check whether the request to patch a courier valid

    :return: list of invalid fields if there are.
    """
    json_dict = json_dict.copy()
    for field in PATCHABLE_FIELDS:
        json_dict.pop(field, None)

    return list(json_dict.keys())


app = Sanic(__name__, log_config=logging_config.LOGGING_CONFIG)
app.blueprint(swagger_blueprint)
app.db = Database()

env = Env()
env.read_env()

app.config.update({
    "API_HOST": f"{env('HOST')}:{env('PORT')}",
    "API_TITLE": "Candy Delivery App",
    "API_DESCRIPTION": "RESTful API that allows to work with delivering",
    "API_CONTACT_EMAIL": "kolobov.kirill@list.ru",
    "API_LICENSE_NAME": " "
})


@app.listener('after_server_start')
async def create_db_connection(app: Sanic, loop) -> None:
    await app.db.connect()


@app.listener('after_server_stop')
async def close_db_connection(app: Sanic, loop) -> None:
    await app.db.close()


@app.post('/couriers')
@doc.tag("Add couriers")
@doc.summary("Add some couriers to the service")
@doc.consumes(doc.JsonBody({"data": [CourierModel.schema()]}), location="body",
              required=True, content_type="application/json")
@doc.response(201, {"couriers": [{"id": int}]},
              description="Couriers added")
@doc.response(400, {"validation_error": {"couriers": [{"id": int}]}},
              description="Some of couriers are invalid")
async def add_couriers(request: Request) -> response.HTTPResponse:
    if not request.json.get('data'):
        return response.json({'couriers': []})

    couriers, invalid_couriers_id = [], []
    for courier in request.json['data']:
        try:
            courier = CourierModel(**courier)
        except ValidationError as e:
            invalid_couriers_id += [courier.get('courier_id', -1)]
            error_logger.error(e.json(indent=4))
        else:
            couriers += [courier]

    if invalid_couriers_id:
        error_logger.error("Request rejected, it contains invalid "
                           f"couriers ({len(invalid_couriers_id)})")
        context = validation_error('couriers', invalid_couriers_id)
        return response.json(context, status=400)

    await app.db.add_couriers(couriers)

    added_couriers = {
        "couriers": [
            {"id": courier.courier_id}
            for courier in couriers
        ]
    }
    return response.json(added_couriers, status=201)


@app.patch('/couriers/<courier_id:int>')
@doc.tag("Update a courier")
@doc.summary("Update some fields of a courier")
@doc.description(f"Update some of {PATCHABLE_FIELDS} of a courier")
@doc.consumes(doc.JsonBody({"regions": List[int], "courier_type": str, "working_hours": str}),
              required=True, location="body", content_type="application/json")
@doc.response(200, CourierModel.schema(), description="Courier updated")
@doc.response(400, None, description="Courier not found or wrong field given")
async def update_courier(request: Request,
                         courier_id: int) -> response.HTTPResponse:
    if invalid_fields := is_json_patching_courier_valid(request.json):
        error_logger.error(f"Only {PATCHABLE_FIELDS} might be "
                           f"updated, but {invalid_fields} found")
        return response.HTTPResponse(status=400)

    courier = await app.db.get_courier(courier_id)

    if not courier:
        error_logger.error(f"Courier ({courier_id}) not found")
        return response.HTTPResponse(status=400)

    courier = CourierModel(**courier.external())

    try:
        courier_data = {**courier.dict(), **request.json}
        updated_courier = CourierModel(**courier_data)
    except ValidationError as e:
        error_logger.error(e.json(indent=4))
        return response.HTTPResponse(status=400)

    await app.db.update_courier(
        courier_id=courier.courier_id,
        **request.json
    )

    return response.json(updated_courier.dict(), indent=4)


@app.get('/couriers/<courier_id:int>')
@doc.tag("Get courier")
@doc.summary("Get info about a courier")
@doc.description("Also calculate additional info: rating, salary")
@doc.response(200, CourierModel.schema().update({"rating": float, "earning": float}),
              description="Courier info calculated and sent")
@doc.response(400, None, description="Courier not found")
async def get_courier(request: Request,
                      courier_id: int) -> response.HTTPResponse:
    courier = await app.db.get_courier(courier_id)
    if not courier:
        error_logger.warning(f"Courier {courier_id=} not found")
        return response.HTTPResponse(status=400)

    # TODO: min, group by region
    # completed_orders = await app.db.get_completed_orders(courier.courier_id)

    return response.json(courier.json_dict(), indent=4)


@app.post('/orders')
@doc.tag("Add orders")
@doc.summary("Add some orders")
@doc.consumes(doc.JsonBody({"data": [OrderModel.schema()]}),
              location="body", required=True)
@doc.response(201, {"orders": [{"id": int}]},
              description="Orders added")
@doc.response(400, {"validation_error": {"orders": [{"id": int}]}},
              description="Some of orders are invalid")
async def add_orders(request: Request) -> response.HTTPResponse:
    orders, invalid_orders_id = [], []
    for order in request.json['data']:
        try:
            order = OrderModel(**order)
        except ValidationError as e:
            invalid_orders_id += [order.get('order_id', -1)]
            error_logger.error(e.json(indent=4))
        else:
            orders += [order]

    if invalid_orders_id:
        error_logger.error("Request rejected, it contains invalid "
                           f"orders ({len(invalid_orders_id)})")
        context = validation_error('orders', invalid_orders_id)
        return response.json(context, status=400)

    await app.db.add_orders(orders)

    added_orders = {
        "orders": [
            {"id": order.order_id}
            for order in orders
        ]
    }
    return response.json(added_orders, status=201)


@app.post('/orders/assign')
@doc.tag("Assign orders")
@doc.summary("Assign all valid orders to the courier by his id")
@doc.consumes(doc.JsonBody({"courier_id": int}), location="body",
              required=True, content_type="application/json")
@doc.response(400, None, description="The courier not found")
@doc.response(200, {"orders": [{"id": int}], "assign_time": str},
              description="Orders assigned to the courier")
async def assign(request: Request) -> response.HTTPResponse:
    courier_id = request.json.get('courier_id', -1)

    if (courier := await app.db.get_courier(courier_id)) is None:
        error_logger.error(f"Courier with {courier_id=} not found")
        return response.HTTPResponse(status=400)

    assigned_orders = await app.db.assign_orders(courier)
    return response.json(assigned_orders)


@app.post('/orders/complete')
@doc.tag("Complete order")
@doc.summary("Complete the order")
@doc.consumes(doc.JsonBody(CompleteModel.schema()), location="body",
              required=True, content_type="application/json")
@doc.response(400, None, description="The request is invalid")
@doc.response(200, {"order_id": int}, description="Order completed")
async def complete(request: Request) -> response.HTTPResponse:
    try:
        complete = CompleteModel(**request.json)
    except ValidationError as e:
        error_logger.error(f"Invalid complete request\n{e.json(indent=4)}")
        return response.HTTPResponse(status=400)

    if (courier := await app.db.get_courier(complete.courier_id)) is None:
        error_logger.error(f"Courier with {complete.courier_id} not found")
        return response.HTTPResponse(status=400)
    if (order := await app.db.get_order(complete.order_id)) is None:
        error_logger.error(f"Order with {complete.order_id} not found")
        return response.HTTPResponse(status=400)

    if (assign_info := await app.db.status(order.order_id)) is None:
        error_logger.error(f"Order {order.order_id} was not assigned")
        return response.HTTPResponse(status=400)

    if (assigned_courier := assign_info.courier.courier_id) != courier.courier_id:
        error_logger.error(
            f"{order.order_id=} assigned to {assigned_courier.courier_id} "
            f"courier, but {courier.courier_id} found"
        )
        return response.HTTPResponse(status=400)

    await app.db.complete_order(complete)

    return response.json(complete.dict(include={'courier_id'}))


@app.get('/')
@doc.exclude(True)
async def home(request: Request) -> response.HTTPResponse:
    return response.json({"ok": True})


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
    return response.json(context, indent=4, status=500)


if __name__ == "__main__":
    debug = env.bool('DEBUG', False)

    workers = 1 if debug else os.cpu_count()
    logger_level = 'DEBUG' if debug else 'INFO'

    logging.getLogger('sanic.root').setLevel(logger_level)
    logging.getLogger('sanic.access').setLevel(logger_level)

    app.run(
        host=env('HOST'),
        port=env.int('PORT'),
        debug=debug,
        workers=workers,
        auto_reload=True
    )
