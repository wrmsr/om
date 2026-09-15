import datetime
import typing as ta
import uuid

from .... import check
from ...dtypes.codecs import BaseDtypeCodec
from ...dtypes.codecs import as_utc_datetime


##


class SqliteDtypeCodec(BaseDtypeCodec):
    """Sqlite stores uuids and datetimes as text and booleans as integers; datetimes are iso strings with an offset."""

    def encode_datetime(self, v: datetime.datetime) -> ta.Any:
        return super().encode_datetime(v).isoformat()

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
