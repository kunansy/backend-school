from datetime import time, datetime
from typing import Any

from pydantic import BaseModel, conlist, validator, conint, \
    confloat

from src import db_api


VALIDATION_ERROR_TEMPLATE = {
    "validation_error": {}
}


def validation_error(field_name: str,
                     ids: list[int]) -> dict:
    error_message = VALIDATION_ERROR_TEMPLATE.copy()
    error_message['validation_error'][field_name] = [
        {"id": id_}
        for id_ in ids
    ]

    return error_message


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

    def is_intercept(self, other) -> bool:
        return self.start > other.start and self.stop < other.stop

    def __or__(self, other) -> bool:
        return self.is_intercept(other)

    def __repr__(self) -> str:
        return f"{self.start.strftime(self.TIME_FORMAT)}-" \
               f"{self.stop.strftime(self.TIME_FORMAT)}"


class CourierModel(BaseModel):
    class Config:
        extra = 'forbid'

    courier_id: conint(strict=True, gt=0)
    courier_type: str
    regions: conlist(item_type=conint(strict=True, gt=0))
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

    @classmethod
    def schema(cls) -> dict[str, Any]:
        return {
            "courier_id": int,
            "courier_type": str,
            "regions": list[int],
            "working_hours": list[str]
        }


class OrderModel(BaseModel):
    class Config:
        extra = 'forbid'

    order_id: conint(strict=True, gt=0)
    weight: confloat(ge=0.01, le=50)
    region: conint(strict=True, gt=0)
    delivery_hours: list[str]

    @validator('delivery_hours')
    def delivery_hours_validator(cls,
                                 value: list[str]) -> list[TimeSpan]:
        return [
            TimeSpan(working_hours)
            for working_hours in value
        ]

    @classmethod
    def schema(cls) -> dict[str, Any]:
        return {
            "order_id": int,
            "weight": float,
            "region": int,
            "delivery_hours": list[str]
        }


class CompleteModel(BaseModel):
    """ The model is expected to represent `complete` requests """
    class Config:
        extra = 'forbid'

    courier_id: conint(strict=True, gt=0)
    order_id: conint(strict=True, gt=0)
    complete_time: str

    @validator('complete_time')
    def complete_time_validator(cls,
                                value: str):
        # TODO: here there's ISO<bla-bla-bla> standard
        return value

    @classmethod
    def schema(cls) -> dict[str, Any]:
        return {
            "courier_id": int,
            "order_id": int,
            "complete_time": str
        }
