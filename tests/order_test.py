import pytest
from pydantic import ValidationError

from src.model import OrderModel, TimeSpan


TEST_DATA = {
    "order_id": 3,
    "weight": 13.56,
    "region": 11,
    "delivery_hours": ['12:10-14:56']
}


def test_right_fields():
    order = OrderModel(**TEST_DATA)

    expected_delivery_hours = TimeSpan(TEST_DATA['delivery_hours'][0])

    assert order.order_id == TEST_DATA['order_id']
    assert order.weight == TEST_DATA['weight']
    assert order.region == TEST_DATA['region']

    # TODO: wtf, just '==' doesn't work
    assert order.delivery_hours[0].start == expected_delivery_hours.start
    assert order.delivery_hours[0].stop == expected_delivery_hours.stop


def test_extra_fields():
    with pytest.raises(ValidationError):
        OrderModel(field='value', **TEST_DATA)


def test_lack_of_fields():
    test_data = TEST_DATA.copy()
    test_data.pop('region')

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


def test_float_id():
    test_data = TEST_DATA.copy()
    test_data['order_id'] = 12.98

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


def test_string_id():
    test_data = TEST_DATA.copy()
    test_data['order_id'] = '12'

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


def test_zero_id():
    test_data = TEST_DATA.copy()
    test_data['order_id'] = 0

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


def test_negative_id():
    test_data = TEST_DATA.copy()
    test_data['order_id'] = -1

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


def test_int_weight():
    test_data = TEST_DATA.copy()
    test_data['weight'] = 12

    order = OrderModel(**test_data)
    assert order.weight == 12


def test_string_weight():
    test_data = TEST_DATA.copy()
    test_data['weight'] = '13.56'

    order = OrderModel(**test_data)
    assert order.weight == 13.56


def test_zero_weight():
    test_data = TEST_DATA.copy()
    test_data['weight'] = 0

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


def test_negative_weight():
    test_data = TEST_DATA.copy()
    test_data['weight'] = -1

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


def test_big_weight():
    test_data = TEST_DATA.copy()
    test_data['weight'] = 51

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


def test_exactly_max_weight():
    test_data = TEST_DATA.copy()
    test_data['weight'] = 50

    order = OrderModel(**test_data)
    assert order.weight == 50


def test_exactly_min_weight():
    test_data = TEST_DATA.copy()
    test_data['weight'] = 0.01

    order = OrderModel(**test_data)
    assert order.weight == 0.01


def test_string_region():
    test_data = TEST_DATA.copy()
    test_data['region'] = '51'

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


def test_float_region():
    test_data = TEST_DATA.copy()
    test_data['region'] = 11.2

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


def test_zero_region():
    test_data = TEST_DATA.copy()
    test_data['region'] = 0

    with pytest.raises(ValidationError):
        OrderModel(**test_data)


def test_negative_region():
    test_data = TEST_DATA.copy()
    test_data['region'] = -1

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

    assert order.delivery_hours[0].start == TimeSpan(delivery_hours[0]).start
    assert order.delivery_hours[0].stop == TimeSpan(delivery_hours[0]).stop

    assert order.delivery_hours[1].start == TimeSpan(delivery_hours[1]).start
    assert order.delivery_hours[1].stop == TimeSpan(delivery_hours[1]).stop

    assert order.delivery_hours[2].start == TimeSpan(delivery_hours[2]).start
    assert order.delivery_hours[2].stop == TimeSpan(delivery_hours[2]).stop


if __name__ == "__main__":
    pytest.main(['-svv'])
