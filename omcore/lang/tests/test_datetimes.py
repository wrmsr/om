import datetime

from ..datetimes import localnow
from ..datetimes import utcfromtimestamp
from ..datetimes import utcnow


def test_aware_datetime_helpers():
    utc = utcnow()
    local = localnow()

    assert utc.tzinfo is datetime.UTC
    assert utc.utcoffset() == datetime.timedelta()
    assert local.tzinfo is not None
    assert local.utcoffset() is not None


def test_utcfromtimestamp():
    assert utcfromtimestamp(0.) == datetime.datetime(1970, 1, 1, tzinfo=datetime.UTC)
