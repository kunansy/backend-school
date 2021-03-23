#!/usr/bin/env python3
import logging

import mock
import pytest

import src.server as server
from src.model import CourierModel
from src.server import app

logging.disable(logging.CRITICAL)


@pytest.fixture(scope="session")
def remove_db():
    server.create_db_connection = print
    server.close_db_connection = print
    del app.db


TEST_COURIERS = {
    "data": [
        {
            "courier_id": 1,
            "courier_type": "foot",
            "regions": [1, 2, 1487],
            "working_hours": ["09:11-12:56", "20:10-23:42"]
        },
        {
            "courier_id": 2,
            "courier_type": "foot",
            "regions": [1487],
            "working_hours": ["23:11-23:12"]
        },
        {
            "courier_id": 13,
            "courier_type": "bike",
            "regions": [145, 197, 17],
            "working_hours": ["09:11-12:56"]
        },
        {
            "courier_id": 45,
            "courier_type": "car",
            "regions": [],
            "working_hours": []
        },
    ]
}

TEST_INVALID_COURIERS = {
    "data": [
        {
            "courier_id": 1,
            "courier_type": "fot",
            "regions": [1, 2, 1487],
            "working_hours": ["09:11-12:56", "20:10-23:42"]
        },
        {
            "courier_id": -2,
            "courier_type": "foot",
            "regions": [1487],
            "working_hours": ["23:11-23:12"]
        },
        {
            "courier_id": 13,
            "courier_type": "bike",
            "regions": [-197, 17],
            "working_hours": ["09:11-12:56"]
        },
        {
            "courier_id": 45,
            "courier_type": "car",
            "regions": [],
            "working_hours": ['today']
        },
        {
            "courier_id": 46,
            "courier_type": "car",
            "regions": [],
            "working_hours": []
        },
    ]
}


@mock.patch("src.server.app.db.add_couriers")
def test_add_couriers_with_valid_couriers(db_mock: mock.AsyncMock):
    json = TEST_COURIERS.copy()
    expected_couriers = [
        CourierModel(**courier)
        for courier in json['data']
    ]
    expected_resp_json = {
        "couriers": [
            {"id": courier.courier_id}
            for courier in expected_couriers
        ]
    }

    request, response = app.test_client.post('/couriers', json=json)

    db_mock.assert_awaited_with(expected_couriers)

    assert response.status == 201
    assert response.json == expected_resp_json


def test_add_couriers_with_invalid_couriers():
    json = TEST_INVALID_COURIERS.copy()
    expected_response_json = {
        'validation_error': {
            'couriers': [{'id': 1}, {'id': -2}, {'id': 13}, {'id': 45}]
        }
    }

    request, response = app.test_client.post('/couriers', json=json)

    assert response.status == 400
    assert response.json == expected_response_json


@mock.patch("src.server.app.db.get_courier")
def test_update_courier_with_no_courier(get_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.app.db.get_courier")
def test_update_courier_with_unpatchable_fields(get_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.app.db.get_courier")
def test_update_courier_with_invalid_fields(get_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.app.db.get_courier")
def test_update_courier_with_invalid_fields(get_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.app.db.get_courier")
@mock.patch("src.server.app.db.update_courier")
def test_update_courier_with_ok(get_courier_mock: mock.AsyncMock,
                                update_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.app.db.get_courier")
def test_get_courier(get_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.app.db.add_orders")
def test_add_orders_with_valid_orders(add_orders_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.app.db.add_orders")
def test_add_orders_with_invalid_orders(add_orders_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.app.db.get_courier")
def test_assign_with_no_courier(get_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.app.db.get_courier")
@mock.patch("src.server.app.db.assign_orders")
def test_assign_with_no_orders(get_courier_mock: mock.AsyncMock,
                               assign_orders_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.app.db.get_courier")
@mock.patch("src.server.app.db.assign_orders")
def test_assign_with_ok(get_courier_mock: mock.AsyncMock,
                        assign_orders_mock: mock.AsyncMock):
    pass


def test_complete_with_invalid_request():
    pass


if __name__ == '__main__':
    pytest.main(['-svv'])
