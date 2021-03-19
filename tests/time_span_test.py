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
    pass


def test_intercept_equal_to_or_with_false():
    pass


def test_not_intercepting_spans():
    pass


def test_equal_spans():
    pass


def test_intercepting_spans():
    pass


def test_spans_with_the_same_start():
    pass


def test_spans_with_the_same_stop():
    pass


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
