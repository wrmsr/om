"""
Value translation between a backend driver's representation and one canonical python form per dtype: int, str, a
tz-aware datetime, uuid.UUID, bool, float, bytes, and for json whatever the document parses to. None passes through in
both directions. A backend that already speaks the canonical forms (postgres) overrides next to nothing; others override
only the dtypes they represent differently.
"""
import abc
import datetime
import typing as ta
import uuid

from ... import check
from ... import lang
from ...formats.json import all as json
from .dtypes import Boolean
from .dtypes import Bytes
from .dtypes import Datetime
from .dtypes import Dtype
from .dtypes import Float
from .dtypes import Integer
from .dtypes import Json
from .dtypes import String
from .dtypes import Uuid


##


class DtypeCodec(lang.Abstract):
    @abc.abstractmethod
    def encode(self, dt: Dtype, v: ta.Any) -> ta.Any:
        """Canonical python value to driver parameter."""

        raise NotImplementedError

    @abc.abstractmethod
    def decode(self, dt: Dtype, v: ta.Any) -> ta.Any:
        """Driver result value to canonical python value."""

        raise NotImplementedError


class BaseDtypeCodec(DtypeCodec, lang.Abstract):
    """Dispatches by dtype to per-kind hooks, each of which defaults to the canonical form itself."""

    def encode(self, dt: Dtype, v: ta.Any) -> ta.Any:
        if v is None:
            return None
        elif isinstance(dt, Integer):
            return self.encode_integer(check.isinstance(v, int))
        elif isinstance(dt, String):
            return self.encode_string(check.isinstance(v, str))
        elif isinstance(dt, Datetime):
            return self.encode_datetime(check.isinstance(v, datetime.datetime))
        elif isinstance(dt, Uuid):
            return self.encode_uuid(check.isinstance(v, uuid.UUID))
        elif isinstance(dt, Boolean):
            return self.encode_boolean(check.isinstance(v, bool))
        elif isinstance(dt, Float):
            return self.encode_float(check.isinstance(v, (float, int)))
        elif isinstance(dt, Bytes):
            return self.encode_bytes(check.isinstance(v, bytes))
        elif isinstance(dt, Json):
            return self.encode_json(v)
        else:
            raise TypeError(dt)

    def decode(self, dt: Dtype, v: ta.Any) -> ta.Any:
        if v is None:
            return None
        elif isinstance(dt, Integer):
            return self.decode_integer(v)
        elif isinstance(dt, String):
            return self.decode_string(v)
        elif isinstance(dt, Datetime):
            return self.decode_datetime(v)
        elif isinstance(dt, Uuid):
            return self.decode_uuid(v)
        elif isinstance(dt, Boolean):
            return self.decode_boolean(v)
        elif isinstance(dt, Float):
            return self.decode_float(v)
        elif isinstance(dt, Bytes):
            return self.decode_bytes(v)
        elif isinstance(dt, Json):
            return self.decode_json(v)
        else:
            raise TypeError(dt)

    #

    def encode_integer(self, v: int) -> ta.Any:
        return v

    def decode_integer(self, v: ta.Any) -> int:
        return check.isinstance(v, int)

    #

    def encode_string(self, v: str) -> ta.Any:
        return v

    def decode_string(self, v: ta.Any) -> str:
        return check.isinstance(v, str)

    #

    def encode_datetime(self, v: datetime.datetime) -> ta.Any:
        check.arg(v.tzinfo is not None, 'canonical datetimes are tz-aware')
        return v

    def decode_datetime(self, v: ta.Any) -> datetime.datetime:
        return as_utc_datetime(check.isinstance(v, datetime.datetime))

    #

    def encode_uuid(self, v: uuid.UUID) -> ta.Any:
        return v

    def decode_uuid(self, v: ta.Any) -> uuid.UUID:
        return check.isinstance(v, uuid.UUID)

    #

    def encode_boolean(self, v: bool) -> ta.Any:
        return v

    def decode_boolean(self, v: ta.Any) -> bool:
        return check.isinstance(v, bool)

    #

    def encode_float(self, v: float) -> ta.Any:
        return float(v)

    def decode_float(self, v: ta.Any) -> float:
        return float(check.isinstance(v, (float, int)))

    #

    def encode_bytes(self, v: bytes) -> ta.Any:
        return v

    def decode_bytes(self, v: ta.Any) -> bytes:
        return bytes(check.isinstance(v, (bytes, bytearray, memoryview)))

    #

    def encode_json(self, v: ta.Any) -> ta.Any:
        # The one kind which does not default to its canonical form, as no driver takes that for every document there
        # is: handed a list one makes an array of it, and handed a str takes it for the text of a document rather than
        # the document. The text is what they all take - as such where documents are kept as text, and read by the
        # server as the document where they are not.
        return json.dumps_compact(v)

    def decode_json(self, v: ta.Any) -> ta.Any:
        return json.loads(check.isinstance(v, (str, bytes)))


##


def as_utc_datetime(v: datetime.datetime) -> datetime.datetime:
    """A naive datetime is taken to be utc; an aware one is normalized to utc."""

    if v.tzinfo is None:
        return v.replace(tzinfo=datetime.UTC)
    return v.astimezone(datetime.UTC)
