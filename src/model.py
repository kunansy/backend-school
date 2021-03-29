from datetime import datetime
from typing import Any, Dict, List

from pydantic import BaseModel, conlist, validator, conint, \
    confloat


DATE_FORMAT = "%Y-%m-%dT%H:%M:%S.%fZ"
POSSIBLE_COURIER_TYPES = [
    'foot', 'bike', 'car'
]


def validate_time(time: str) -> str:
    start, stop = time.split('-')

    start = datetime.strptime(start, "%H:%M").time()
    stop = datetime.strptime(stop, "%H:%M").time()

    if start >= stop:
        raise ValueError

    return time


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
        if (value := value.lower()) in POSSIBLE_COURIER_TYPES:
            return value
        raise ValueError

    @validator('working_hours')
    def working_hours_validator(cls,
                                value: List[str]) -> List[str]:
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
