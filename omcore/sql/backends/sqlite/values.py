import datetime
import typing as ta
import uuid

from .... import check
from ...dtypes.codecs import BaseDtypeCodec
from ...dtypes.codecs import as_utc_datetime


##


class SqliteDtypeCodec(BaseDtypeCodec):
    """
    Sqlite stores uuids and datetimes as text and booleans as integers. A datetime is written as utc in the same
    space-separated form sqlite's own timestamps take - current_timestamp's seconds, the milliseconds of the default the
    tabledefs give a column - so they all sort together as text; any of them (and an iso 'T' with an offset) reads back.
    """

    def encode_datetime(self, v: datetime.datetime) -> ta.Any:
        return as_utc_datetime(super().encode_datetime(v)).strftime('%Y-%m-%d %H:%M:%S.%f')

    def decode_datetime(self, v: ta.Any) -> datetime.datetime:
        if isinstance(v, datetime.datetime):
            return as_utc_datetime(v)
        return as_utc_datetime(datetime.datetime.fromisoformat(check.isinstance(v, str)))

    #

    def encode_uuid(self, v: uuid.UUID) -> ta.Any:
        return str(v)

    def decode_uuid(self, v: ta.Any) -> uuid.UUID:
        if isinstance(v, uuid.UUID):
            return v
        return uuid.UUID(check.isinstance(v, str))

    #

    def encode_boolean(self, v: bool) -> ta.Any:
        return int(v)

    def decode_boolean(self, v: ta.Any) -> bool:
        if isinstance(v, bool):
            return v
        return bool(check.isinstance(v, int))
