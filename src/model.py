from __future__ import annotations

from datetime import time, datetime

from pydantic import BaseModel, PositiveInt, conlist, validator

from src import db_api


class TimeSpan:
    TIME_FORMAT = "%H:%M"

    def __init__(self,
                 value: str) -> None:
        start, stop = value.split('-')

        self.__start = TimeSpan.parse_time(start)
        self.__stop = TimeSpan.parse_time(stop)

        if start >= stop:
            raise ValueError("Start must me be less than stop")

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

    def is_intercept(self,
                     other: TimeSpan) -> bool:
        return self.start > other.start and self.stop < other.stop

    def __or__(self, 
               other: TimeSpan) -> bool:
        return self.is_intercept(other)

    def __repr__(self) -> str:
        return f"{self.start.strftime(self.TIME_FORMAT)}-" \
               f"{self.stop.strftime(self.TIME_FORMAT)}"


class CourierModel(BaseModel):
    courier_id: PositiveInt()
    courier_type: str
    regions: conlist(item_type=PositiveInt())
    working_hours: list[str]

    @validator('courier_type')
    def courier_type_validator(cls,
                               value: str) -> str:
        possible_courier_types = db_api.get_courier_types()

        if (value := value.lower()) in possible_courier_types:
            return value
        raise ValueError

    @validator('working_hours')
    def working_hours_validator(cls,
                                value: list[str]) -> list[TimeSpan]:
        # TODO: ISO 8601, RFC 3339
        return [
            TimeSpan(working_hours)
            for working_hours in value
        ]


class OrderModel(BaseModel):
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
    def delivery_hours_validator(cls,
                                 value: list[str]) -> list[TimeSpan]:
        return [
            TimeSpan(working_hours)
            for working_hours in value
        ]
