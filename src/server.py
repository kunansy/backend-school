#!/usr/bin/env python3
import logging
import os
from datetime import datetime, time

from environs import Env
from pydantic import BaseModel, validator, conlist, PositiveInt
from sanic import Sanic, response
from sanic.request import Request
from uvloop.loop import Loop

import db_api
import logger


app = Sanic(__name__, log_config=logger.LOGGING_CONFIG)
env = Env()
env.read_env()


class TimeSpan:
    TIME_FORMAT = "%H:%M"

    def __init__(self,
                 value: str) -> None:
        start, stop = value.split('-')

        self.__start = TimeSpan.parse_time(start)
        self.__stop = TimeSpan.parse_time(stop)

    @property
    def start(self) -> time:
        return self.__start

    @property
    def stop(self) -> time:
        return self.__stop

    @classmethod
    def parse_time(cls,
                   time_string: str) -> time:
        return datetime.strptime(time_string, cls.TIME_FORMAT).time()

    def is_intercept(self, other) -> bool:
        return self.start >= other.start and self.stop <= other.stop

    def __or__(self, other) -> bool:
        return self.is_intercept(other)

    def __repr__(self) -> str:
        return f"{self.start}-{self.stop}"


class Courier(BaseModel):
    courier_id: PositiveInt()
    courier_type: str
    regions: conlist(item_type=PositiveInt())
    working_hours: conlist(item_type=str)

    @validator('courier_type')
    def courier_type_validator(cls, value: str) -> str:
        possible_courier_types = db_api.get_courier_types()

        if (value := value.lower()) not in possible_courier_types:
            raise ValueError
        return value

    @validator('working_hours')
    def working_hours_validator(cls, value: list[str]) -> list[TimeSpan]:
        # TODO: ISO 8601, RFC 3339
        return [
            TimeSpan(working_hours)
            for working_hours in value
        ]


class Order(BaseModel):
    order_id: PositiveInt()
    weight: PositiveInt()
    region: PositiveInt()
    delivery_hours: list[str]

    @validator('weight')
    def weight_validator(cls,
                         value: int) -> int:
        if 0.01 <= value <= 50:
            return value
        raise ValueError

    @validator('delivery_hours')
    def working_hours_validator(cls,
                                value: list[str]) -> list[TimeSpan]:
        return [
            TimeSpan(working_hours)
            for working_hours in value
        ]


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
    pass


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
