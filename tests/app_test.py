#!/usr/bin/env python3
import mock
import pytest
import src.server as server


@mock.patch("src.server.db_api.add_couriers")
def test_add_couriers_with_valid_couriers(db_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.db_api.add_couriers")
def test_add_couriers_with_invalid_couriers(db_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.db_api.get_courier")
def test_update_courier_with_no_courier(get_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.db_api.get_courier")
def test_update_courier_with_unpatchable_fields(get_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.db_api.get_courier")
def test_update_courier_with_invalid_fields(get_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.db_api.get_courier")
def test_update_courier_with_invalid_fields(get_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.db_api.get_courier")
@mock.patch("src.server.db_api.update_courier")
def test_update_courier_with_ok(get_courier_mock: mock.AsyncMock,
                                update_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.db_api.get_courier")
def test_get_courier(get_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.db_api.add_orders")
def test_add_orders_with_valid_orders(add_orders_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.db_api.add_orders")
def test_add_orders_with_invalid_orders(add_orders_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.db_api.get_courier")
def test_assign_with_no_courier(get_courier_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.db_api.get_courier")
@mock.patch("src.server.db_api.assign_orders")
def test_assign_with_no_orders(get_courier_mock: mock.AsyncMock,
                               assign_orders_mock: mock.AsyncMock):
    pass


@mock.patch("src.server.db_api.get_courier")
@mock.patch("src.server.db_api.assign_orders")
def test_assign_with_ok(get_courier_mock: mock.AsyncMock,
                        assign_orders_mock: mock.AsyncMock):
    pass


def test_complete_with_invalid_request():
    pass


if __name__ == '__main__':
    pytest.main(['-svv'])
