import datetime

from ...globals import marshal
from ...globals import unmarshal


def test_datetime_roundtrip():
    dt = datetime.datetime(2020, 5, 17, 12, 34, 56, 789000)  # noqa: DTZ001
    assert unmarshal(marshal(dt), datetime.datetime) == dt


def test_date_roundtrip():
    # Dates marshal with a (zero) time component but must still roundtrip.
    d = datetime.date(2020, 5, 17)
    assert unmarshal(marshal(d), datetime.date) == d
    assert unmarshal('2020-05-17', datetime.date) == d


def test_time_roundtrip():
    # Times marshal with a (1900-01-01) date component but must still roundtrip.
    t = datetime.time(12, 34, 56)
    assert unmarshal(marshal(t), datetime.time) == t
    assert unmarshal('12:34:56', datetime.time) == t


def test_timedelta_roundtrip():
    td = datetime.timedelta(days=1, hours=2, minutes=3, seconds=4)
    assert unmarshal(marshal(td), datetime.timedelta) == td
