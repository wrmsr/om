import datetime
import decimal

import pytest

from .. import converters
from ..errors import ProgrammingError


def test_escape_string():
    assert converters.escape_string('foo\nbar') == 'foo\\nbar'


def test_convert_datetime():
    expected = datetime.datetime(2007, 2, 24, 23, 6, 20)
    dt = converters.convert_datetime('2007-02-24 23:06:20')
    assert dt == expected


def test_convert_datetime_with_fsp():
    expected = datetime.datetime(2007, 2, 24, 23, 6, 20, 511581)
    dt = converters.convert_datetime('2007-02-24 23:06:20.511581')
    assert dt == expected


def _check_convert_timedelta(*, with_negate=False, with_fsp=False):
    d = {'hours': 789, 'minutes': 12, 'seconds': 34}
    s = '%(hours)s:%(minutes)s:%(seconds)s' % d
    if with_fsp:
        d['microseconds'] = 511581
        s += '.%(microseconds)s' % d

    expected = datetime.timedelta(**d)
    if with_negate:
        expected = -expected
        s = '-' + s

    tdelta = converters.convert_timedelta(s)
    assert tdelta == expected


def test_convert_timedelta():
    _check_convert_timedelta(with_negate=False, with_fsp=False)
    _check_convert_timedelta(with_negate=True, with_fsp=False)


def test_convert_timedelta_with_fsp():
    _check_convert_timedelta(with_negate=False, with_fsp=True)
    _check_convert_timedelta(with_negate=True, with_fsp=True)


def test_escape_timedelta():
    # MySQL TIME allows negatives, and a timedelta is the registered param encoder, so a negative value must escape to
    # its real magnitude with a single leading sign - not with complemented sub-hour fields.
    cases = {
        datetime.timedelta(hours=1, minutes=30): "'01:30:00'",
        datetime.timedelta(days=1, hours=2): "'26:00:00'",
        -datetime.timedelta(minutes=30): "'-00:30:00'",
        -datetime.timedelta(hours=1, minutes=30): "'-01:30:00'",
        datetime.timedelta(seconds=83579, microseconds=51000): "'23:12:59.051000'",
        -datetime.timedelta(seconds=83579, microseconds=51000): "'-23:12:59.051000'",
    }
    for tdelta, expected in cases.items():
        assert converters.escape_timedelta(tdelta) == expected
        # The escaped literal must re-parse to the same duration.
        assert converters.convert_timedelta(converters.escape_timedelta(tdelta).strip("'")) == tdelta


def test_convert_time():
    expected = datetime.time(23, 6, 20)
    time_obj = converters.convert_time('23:06:20')
    assert time_obj == expected


def test_convert_time_with_fsp():
    expected = datetime.time(23, 6, 20, 511581)
    time_obj = converters.convert_time('23:06:20.511581')
    assert time_obj == expected


def test_decimal_special_values():
    values = (
        decimal.Decimal('NaN'),
        decimal.Decimal('sNaN'),
        decimal.Decimal('Infinity'),
        decimal.Decimal('-Infinity'),
    )
    for value in values:
        with pytest.raises(ProgrammingError, match=f'{str(value).lower()} can not be used with MySQL'):
            converters.Decimal2Literal(value, None)
