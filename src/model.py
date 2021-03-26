from datetime import time, datetime
from typing import Any, Dict, List

from pydantic import BaseModel, conlist, validator, conint, \
    confloat


VALIDATION_ERROR_TEMPLATE = {
    "validation_error": {}
}
DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"


def validation_error(field_name: str,
                     ids: List[int]) -> dict:
    error_message = VALIDATION_ERROR_TEMPLATE.copy()
    error_message['validation_error'][field_name] = [
        {"id": id_}
        for id_ in ids
    ]

    return error_message


def validate_time(time_: str) -> str:
    start, stop = time_.split('-')

    start = datetime.strptime(start, "%H:%M").time()
    stop = datetime.strptime(stop, "%H:%M").time()

    if start >= stop:
        raise ValueError

    return time_


class CourierModel(BaseModel):
    class Config:
        extra = 'forbid'

    courier_id: conint(strict=True, gt=0)
    courier_type: str
    regions: conlist(item_type=conint(strict=True, gt=0))
    working_hours: List[str]

    @validator('courier_type')
    def courier_type_validator(cls,
                               value: str) -> str:
        possible_courier_types = ['foot', 'bike', 'car']

        if (value := value.lower()) in possible_courier_types:
            return value
        raise ValueError

    @validator('working_hours')
    def working_hours_validator(cls,
                                value: List[str]) -> List[str]:
        # TODO: ISO 8601, RFC 3339
        return [
            validate_time(working_hours)
            for working_hours in value
        ]

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        return {
            "courier_id": int,
            "courier_type": str,
            "regions": List[int],
            "working_hours": List[str]
        }

    def __eq__(self, other) -> bool:
        return (self.courier_id == other.courier_id and
                self.courier_type == other.courier_type and
                self.regions == other.regions and
                self.working_hours == other.working_hours)
        # TODO: wtf: this code doesn't work, I mean it
        #  returns false when items are equal
        # return all(
        #     getattr(other, name) == value
        #     for name, value in self.__fields__.items()
        # )


class OrderModel(BaseModel):
    class Config:
        extra = 'forbid'

    order_id: conint(strict=True, gt=0)
    weight: confloat(ge=0.01, le=50)
    region: conint(strict=True, gt=0)
    delivery_hours: List[str]

    @validator('delivery_hours')
    def delivery_hours_validator(cls,
                                 value: List[str]) -> List[str]:
        return [
            validate_time(working_hours)
            for working_hours in value
        ]

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        return {
            "order_id": int,
            "weight": float,
            "region": int,
            "delivery_hours": List[str]
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
                                value: str) -> str:
        datetime.strptime(value, DATE_FORMAT)
        return value

    @classmethod
    def schema(cls) -> Dict[str, Any]:
        return {
            "courier_id": int,
            "order_id": int,
            "complete_time": str
        }
