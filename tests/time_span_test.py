#!/usr/bin/env python3
from datetime import time

import pytest

from src.db_api import TimeSpan


@pytest.mark.parametrize(
    'value', (
        '12:35_12:36', '12.00-13.00',
        '27:00-12:00', '12:56-13:66',
        '12:00-06:59', ''
    )
)
def test_wrong_format(value):
    with pytest.raises(ValueError):
        TimeSpan(value)


@pytest.mark.parametrize(
    ('t1', 't2', 'result'), (
        ('12:10-13:50', '13:40-14:10', True),
        ('12:10-12:20', '12:10-12:20', True),
        ('21:55-23:15', '22:00-23:45', True),
        ('10:55-23:15', '12:00-19:45', True),
        ('12:10-12:20', '12:21-12:50', False),
        ('12:10-12:20', '12:21-12:50', False),
        ('12:10-12:20', '06:21-10:50', False),
    )
)
def test_intercepting(t1, t2, result):
    t1, t2 = TimeSpan(t1), TimeSpan(t2)

    assert t1.is_intercept(t2) is t1 | t2 is result
    assert t2.is_intercept(t1) is t2 | t1 is result


@pytest.mark.parametrize(
    ('t1', 't2', 'result', 'time_', 'attr'), (
        ('21:55-22:15', '21:55-23:45', True, time(21, 55), 'start'),
        ('10:31-20:50', '17:55-20:50', True, time(20, 50), 'stop')
    )
)
def test_spans_with_the_same_start_or_stop(t1, t2, result, time_, attr):
    t1, t2 = TimeSpan(t1), TimeSpan(t2)

    assert t1 | t2 is result
    assert t2 | t1 is result
    assert getattr(t1, attr) == getattr(t2, attr) == time_


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
