import datetime
import typing as ta
import uuid

from .... import check
from ...dtypes.codecs import BaseDtypeCodec
from ...dtypes.codecs import as_utc_datetime


##


class MysqlDtypeCodec(BaseDtypeCodec):
    """
    Mysql stores uuids as char(36) and booleans as tinyint, and its datetime column has no zone: values are written as
    naive utc and read back as utc.
    """

    def encode_datetime(self, v: datetime.datetime) -> ta.Any:
        return as_utc_datetime(super().encode_datetime(v)).replace(tzinfo=None)

    def decode_datetime(self, v: ta.Any) -> datetime.datetime:
        return as_utc_datetime(check.isinstance(v, datetime.datetime))

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
