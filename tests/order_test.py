#!/usr/bin/env python3
import pytest
from pydantic import ValidationError

from src.model import OrderModel


TEST_DATA = {
    "order_id": 3,
    "weight": 13.56,
    "region": 11,
    "delivery_hours": ['12:10-14:56']
}


def test_right_fields():
    order = OrderModel(**TEST_DATA)

    assert order.order_id == TEST_DATA['order_id']
    assert order.weight == TEST_DATA['weight']
    assert order.region == TEST_DATA['region']
    assert order.delivery_hours == TEST_DATA['delivery_hours']


def test_extra_fields():
    with pytest.raises(ValidationError):
        OrderModel(field='value', **TEST_DATA)


def test_lack_of_fields():
    test_data = TEST_DATA.copy()
    test_data.pop('region')

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


@pytest.mark.parametrize(
    'value', (12.97, '12', 0, -1)
)
def test_wrong_id(value):
    test_data = TEST_DATA.copy()
    test_data['order_id'] = value

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


@pytest.mark.parametrize(
    ('value', 'expected'), (
        (12, 12), ('13.56', 13.56), (50, 50)
    )
)
def test_right_weight(value, expected):
    test_data = TEST_DATA.copy()
    test_data['weight'] = value

    order = OrderModel(**test_data)
    assert order.weight == expected


@pytest.mark.parametrize(
    'value', (0, -1, 51, 0.009)
)
def test_wrong_weight(value):
    test_data = TEST_DATA.copy()
    test_data['weight'] = value

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


@pytest.mark.parametrize(
    'value', (11.2, 0, -1, '51')
)
def test_wrong_region(value):
    test_data = TEST_DATA.copy()
    test_data['region'] = value

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


def test_not_serializable_delivery_hours():
    test_data = TEST_DATA.copy()
    test_data['delivery_hours'] = ['12_55-13_10']

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


def test_several_delivery_hours():
    test_data = TEST_DATA.copy()
    delivery_hours = ['12:55-13:10', '11:19-12:50', '21:50-23:10']
    test_data['delivery_hours'] = delivery_hours

    order = OrderModel(**test_data)

    assert order.delivery_hours == delivery_hours


if __name__ == "__main__":
    pytest.main(['-svv'])
