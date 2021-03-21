#!/usr/bin/env python3
from datetime import time

import pytest

from src.model import TimeSpan


def test_without_dash():
    with pytest.raises(ValueError):
        TimeSpan('12:35_12:36')


def test_wrong_time_format():
    with pytest.raises(ValueError):
        TimeSpan('12.00-13.00')


def test_wrong_hours():
    with pytest.raises(ValueError):
        TimeSpan('27:00-12:00')


def test_wrong_minutes():
    with pytest.raises(ValueError):
        TimeSpan('12:56-13:66')


def test_start_less_than_stop():
    with pytest.raises(ValueError):
        TimeSpan('12:00-06:59')


def test_intercept_equal_to_or_with_true():
    t1, t2 = TimeSpan('12:10-13:50'), TimeSpan('13:40-14:10')

    assert t1.is_intercept(t2) is t1 | t2 is True
    assert t2.is_intercept(t1) is t2 | t1 is True


def test_intercept_equal_to_or_with_false():
    t1, t2 = TimeSpan('12:10-12:20'), TimeSpan('12:21-12:50')

    assert t1.is_intercept(t2) is t1 | t2 is False
    assert t2.is_intercept(t1) is t2 | t1 is False


def test_equality_of_operands_order():
    t1, t2 = TimeSpan('12:10-12:20'), TimeSpan('12:21-12:50')

    assert t1.is_intercept(t2) is t1 | t2 is False
    assert t2.is_intercept(t1) is t2 | t1 is False


def test_not_intercepting_spans():
    t1, t2 = TimeSpan('12:10-12:20'), TimeSpan('06:21-10:50')

    assert t1 | t2 is False
    assert t2 | t1 is False


def test_equal_spans():
    t1, t2 = TimeSpan('12:10-12:20'), TimeSpan('12:10-12:20')

    assert t1 | t2 is True
    assert t2 | t1 is True


def test_intercepting_spans():
    t1, t2 = TimeSpan('21:55-23:15'), TimeSpan('22:00-23:45')

    assert t1 | t2 is True
    assert t2 | t1 is True


def test_one_span_inside_another():
    t1, t2 = TimeSpan('10:55-23:15'), TimeSpan('12:00-19:45')

    assert t1 | t2 is True
    assert t2 | t1 is True


def test_spans_with_the_same_start():
    t1, t2 = TimeSpan('21:55-22:15'), TimeSpan('21:55-23:45')

    assert t1 | t2 is True
    assert t2 | t1 is True
    assert t1.start == t2.start == time(21, 55)


def test_spans_with_the_same_stop():
    t1, t2 = TimeSpan('10:31-20:50'), TimeSpan('17:55-20:50')

    assert t1 | t2 is True
    assert t2 | t1 is True
    assert t1.stop == t2.stop == time(20, 50)


def test_repr():
    res = "14:44-21:12"

    assert str(TimeSpan(res)) == res


def test_start_property():
    t = TimeSpan('12:50-23:19')

    assert t.start == t._TimeSpan__start


def test_stop_property():
    t = TimeSpan('12:50-23:19')

    assert t.stop == t._TimeSpan__stop


if __name__ == "__main__":
    pytest.main(['-svv'])
