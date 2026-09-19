import datetime
import uuid

from ...dtypes import BOOLEAN
from ...dtypes import BYTES
from ...dtypes import DATETIME
from ...dtypes import FLOAT
from ...dtypes import INTEGER
from ...dtypes import STRING
from ...dtypes import UUID
from ..mysql.values import MysqlDtypeCodec
from ..postgres.values import PostgresDtypeCodec
from ..sqlite.values import SqliteDtypeCodec


_DT = datetime.datetime(2020, 1, 2, 3, 4, 5, 123456, tzinfo=datetime.UTC)
_VALUES = [
    (INTEGER, 42),
    (STRING, 'héllo'),
    (DATETIME, _DT),
    (UUID, uuid.uuid7()),
    (BOOLEAN, True),
    (FLOAT, 1.5),
    (BYTES, b'\x00\xff'),
]


def test_roundtrips():
    for codec in (PostgresDtypeCodec(), SqliteDtypeCodec(), MysqlDtypeCodec()):
        for dt, v in _VALUES:
            assert codec.decode(dt, codec.encode(dt, v)) == v
            assert codec.encode(dt, None) is None and codec.decode(dt, None) is None


def test_sqlite_datetime_text_sorts_with_current_timestamp():
    # the dialect's own current_timestamp is 'YYYY-MM-DD HH:MM:SS'; the codec's form must sort against it as text
    c = SqliteDtypeCodec()
    assert c.encode(DATETIME, _DT) == '2020-01-02 03:04:05.123456'
    assert c.decode(DATETIME, '2020-01-02 03:04:05') == _DT.replace(microsecond=0)
    assert c.decode(DATETIME, '2020-01-02T03:04:05.123456+00:00') == _DT
    assert c.encode(DATETIME, _DT.astimezone(datetime.timezone(datetime.timedelta(hours=5)))) == '2020-01-02 03:04:05.123456'  # noqa
    assert '2020-01-02 03:04:05' < c.encode(DATETIME, _DT) < '2020-01-02 03:04:06'

    # as must the milliseconds of a tabledef default
    assert c.decode(DATETIME, '2020-01-02 03:04:05.123') == _DT.replace(microsecond=123000)
    assert '2020-01-02 03:04:05.123' < c.encode(DATETIME, _DT) < '2020-01-02 03:04:05.124'


def test_mysql_datetime_is_naive_utc():
    c = MysqlDtypeCodec()
    assert c.encode(DATETIME, _DT.astimezone(datetime.timezone(datetime.timedelta(hours=-3)))) == _DT.replace(tzinfo=None)  # noqa
    assert c.decode(DATETIME, _DT.replace(tzinfo=None)) == _DT
