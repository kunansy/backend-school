import pytest
from pydantic import ValidationError

from src.model import CourierModel


TEST_DATA = {
    "courier_id": 12,
    "courier_type": 'foot',
    "regions": [1, 171, 162],
    "working_hours": ['01:10-04:20', '12:50-21:00']
}


def test_right_fields():
    CourierModel(**TEST_DATA)


def test_extra_fields():
    with pytest.raises(ValidationError):
        CourierModel(field='value', **TEST_DATA)


def test_lack_of_fields():
    test_data = TEST_DATA.copy()
    test_data.pop('courier_id')

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


def test_float_id():
    test_data = TEST_DATA.copy()
    test_data['courier_id'] = 12.98

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


def test_string_id():
    test_data = TEST_DATA.copy()
    test_data['courier_id'] = '88'

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


def test_zero_id():
    test_data = TEST_DATA.copy()
    test_data['courier_id'] = 0

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


def test_negative_id():
    test_data = TEST_DATA.copy()
    test_data['courier_id'] = -1

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


def test_wrong_type():
    test_data = TEST_DATA.copy()
    test_data['courier_type'] = 'fot'

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


def test_empty_type():
    test_data = TEST_DATA.copy()
    test_data['courier_type'] = ''

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


def test_float_regions():
    test_data = TEST_DATA.copy()
    test_data['regions'] = [1.12, 3, 12.99]

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


def test_string_regions():
    test_data = TEST_DATA.copy()
    test_data['regions'] = [1, 4, '12']

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


def test_zero_regions():
    test_data = TEST_DATA.copy()
    test_data['regions'] = [0, 1, 5]

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


def test_negative_regions():
    test_data = TEST_DATA.copy()
    test_data['regions'] = [1, 5, -2]

    with pytest.raises(ValidationError):
        CourierModel(**test_data)


def test_empty_regions_list():
    test_data = TEST_DATA.copy()
    test_data['regions'] = []

    CourierModel(**test_data)


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
