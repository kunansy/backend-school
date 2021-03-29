#!/usr/bin/env python3
import pytest
from pydantic import ValidationError

from src.model import CourierModel


TEST_DATA = {
    "courier_id": 12,
    "courier_type": 'foot',
    "regions": [1, 171, 162],
    "working_hours": ['01:10-04:20']
}


def test_right_fields():
    courier = CourierModel(**TEST_DATA)

    assert courier.courier_id == TEST_DATA['courier_id']
    assert courier.courier_type == TEST_DATA['courier_type']
    assert courier.regions == TEST_DATA['regions']
    assert courier.working_hours == TEST_DATA['working_hours']


def test_extra_fields():
    with pytest.raises(ValidationError):
        CourierModel(field='value', **TEST_DATA)


def test_lack_of_fields():
    test_data = TEST_DATA.copy()
    test_data.pop('courier_id')

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


@pytest.mark.parametrize(
    'value', (12.98, '88', 0, -1)
)
def test_wrong_id(value):
    test_data = TEST_DATA.copy()
    test_data['courier_id'] = value

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


@pytest.mark.parametrize(
    'value', ('fot', '')
)
def test_wrong_type(value):
    test_data = TEST_DATA.copy()
    test_data['courier_type'] = value

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


@pytest.mark.parametrize(
    'value', (
        [1.12, 3, 12.99],
        [1, 4, '12'],
        [0, 1, 5],
        [1, 5, -2]
    )
)
def test_float_regions(value):
    test_data = TEST_DATA.copy()
    test_data['regions'] = value

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


def test_empty_regions_list():
    test_data = TEST_DATA.copy()
    test_data['regions'] = []

    courier = CourierModel(**test_data)
    assert courier.regions == []


def test_not_serializable_working_hours():
    test_data = TEST_DATA.copy()
    test_data['working_hours'] = ['12_55-13_10']

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


def test_several_working_hours():
    test_data = TEST_DATA.copy()
    test_data['working_hours'] = ['12:55-13:10', '11:19-12:50', '21:50-23:10']

    CourierModel(**test_data)


if __name__ == "__main__":
    pytest.main(['-svv'])
