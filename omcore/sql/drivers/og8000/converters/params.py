# Copyright (c) 2007-2009, Mathieu Fenniak
# Copyright (c) The Contributors
# All rights reserved.
#
# Redistribution and use in source and binary forms, with or without modification, are permitted provided that the
# following conditions are met:
#
# * Redistributions of source code must retain the above copyright notice, this list of conditions and the following
#   disclaimer.
# * Redistributions in binary form must reproduce the above copyright notice, this list of conditions and the following
#   disclaimer in the documentation and/or other materials provided with the distribution.
# * The name of the author may not be used to endorse or promote products derived from this software without specific
#   prior written permission.
#
# THIS SOFTWARE IS PROVIDED BY THE COPYRIGHT HOLDERS AND CONTRIBUTORS "AS IS" AND ANY EXPRESS OR IMPLIED WARRANTIES,
# INCLUDING, BUT NOT LIMITED TO, THE IMPLIED WARRANTIES OF MERCHANTABILITY AND FITNESS FOR A PARTICULAR PURPOSE ARE
# DISCLAIMED. IN NO EVENT SHALL THE COPYRIGHT OWNER OR CONTRIBUTORS BE LIABLE FOR ANY DIRECT, INDIRECT, INCIDENTAL,
# SPECIAL, EXEMPLARY, OR CONSEQUENTIAL DAMAGES (INCLUDING, BUT NOT LIMITED TO, PROCUREMENT OF SUBSTITUTE GOODS OR
# SERVICES; LOSS OF USE, DATA, OR PROFITS; OR BUSINESS INTERRUPTION) HOWEVER CAUSED AND ON ANY THEORY OF LIABILITY,
# WHETHER IN CONTRACT, STRICT LIABILITY, OR TORT (INCLUDING NEGLIGENCE OR OTHERWISE) ARISING IN ANY WAY OUT OF THE USE
# OF THIS SOFTWARE, EVEN IF ADVISED OF THE POSSIBILITY OF SUCH DAMAGE.
#
# Original Author: Mathieu Fenniak
"""The adapter registries, and the rendering of Python values as query parameters and SQL literals."""

import datetime
import decimal
import enum
import functools
import ipaddress
import typing as ta
import uuid

from ..errors import InterfaceError
from ..types import PGInterval
from ..types import Range
from . import ins
from . import oids
from .adapters import InAdapter
from .adapters import OutAdapter
from .outs import array_string_escape
from .outs import bool_out
from .outs import bytes_out
from .outs import date_out
from .outs import datetime_out
from .outs import enum_out
from .outs import float_out
from .outs import inet_out
from .outs import int_out
from .outs import interval_out
from .outs import json_out
from .outs import null_out
from .outs import numeric_out
from .outs import string_out
from .outs import time_out
from .outs import uuid_out


##


def range_out(v: Range[ta.Any]) -> str:
    if v.is_empty:
        return 'empty'
    else:
        le = v.lower
        val_lower = '' if le is None else make_param(PY_TYPES, le)
        ue = v.upper
        val_upper = '' if ue is None else make_param(PY_TYPES, ue)
        return f'{v.bounds[0]}{val_lower},{val_upper}{v.bounds[1]}'


@functools.singledispatch
def array_out(val: ta.Any) -> str:
    return make_param(PY_TYPES, val)  # type: ignore[return-value]


@array_out.register
def _(val: list) -> str:
    result = [array_out(v) for v in val]
    return f'{{{",".join(result)}}}'


@array_out.register
def _(val: tuple) -> str:
    return f'"{composite_out(val)}"'


@array_out.register
def _(val: None) -> str:
    return 'NULL'


@array_out.register
def _(val: dict) -> str:
    return array_string_escape(json_out(val))


@array_out.register(bytes)
@array_out.register(bytearray)
def _(val: bytes | bytearray) -> str:
    return f'"\\{bytes_out(val)}"'


@array_out.register
def _(val: str) -> str:
    return array_string_escape(val)


@functools.singledispatch
def composite_out(val: ta.Any) -> str:
    return array_out(val)


@composite_out.register
def _(val: tuple) -> str:
    result = [composite_out(v) for v in val]

    return f'({",".join(result)})'


@composite_out.register
def _(val: None) -> str:
    return ''


PY_PG: dict[type, int] = {
    datetime.date: oids.DATE,
    decimal.Decimal: oids.NUMERIC,
    ipaddress.IPv4Address: oids.INET,
    ipaddress.IPv6Address: oids.INET,
    ipaddress.IPv4Network: oids.INET,
    ipaddress.IPv6Network: oids.INET,
    PGInterval: oids.INTERVAL,
    datetime.time: oids.TIME,
    datetime.timedelta: oids.INTERVAL,
    uuid.UUID: oids.UUID_TYPE,
    bool: oids.BOOLEAN,
    bytearray: oids.BYTES,
    dict: oids.JSONB,
    float: oids.FLOAT,
    type(None): oids.NULLTYPE,
    bytes: oids.BYTES,
    str: oids.TEXT,
}


PY_TYPES: dict[type, OutAdapter] = {
    datetime.date: date_out,  # date
    datetime.datetime: datetime_out,
    decimal.Decimal: numeric_out,  # numeric
    enum.Enum: enum_out,  # enum
    ipaddress.IPv4Address: inet_out,  # inet
    ipaddress.IPv6Address: inet_out,  # inet
    ipaddress.IPv4Network: inet_out,  # inet
    ipaddress.IPv6Network: inet_out,  # inet
    # FIXME: interval_out expects a timedelta, so a PGInterval with fields left as None renders as 'None days ...'.
    # pg_interval_out exists for this type.
    PGInterval: interval_out,  # interval
    Range: range_out,  # range types
    datetime.time: time_out,  # time
    datetime.timedelta: interval_out,  # interval
    uuid.UUID: uuid_out,  # uuid
    bool: bool_out,  # bool
    bytearray: bytes_out,  # bytea
    dict: json_out,  # jsonb
    float: float_out,  # float8
    type(None): null_out,  # null
    bytes: bytes_out,  # bytea
    str: string_out,  # unknown
    int: int_out,
    list: array_out,
    tuple: composite_out,
}


PG_TYPES: dict[int, InAdapter] = {
    oids.BIGINT: int,  # int8
    oids.BIGINT_ARRAY: ins.int_array_in,  # int8[]
    oids.BOOLEAN: ins.bool_in,  # bool
    oids.BOOLEAN_ARRAY: ins.bool_array_in,  # bool[]
    oids.BYTES: ins.bytes_in,  # bytea
    oids.BYTES_ARRAY: ins.bytes_array_in,  # bytea[]
    oids.CHAR: ins.string_in,  # char
    oids.CHAR_ARRAY: ins.string_array_in,  # char[]
    oids.CIDR_ARRAY: ins.cidr_array_in,  # cidr[]
    oids.CSTRING: ins.string_in,  # cstring
    oids.CSTRING_ARRAY: ins.string_array_in,  # cstring[]
    oids.DATE: ins.date_in,  # date
    oids.DATE_ARRAY: ins.date_array_in,  # date[]
    oids.DATEMULTIRANGE: ins.datemultirange_in,  # datemultirange
    oids.DATEMULTIRANGE_ARRAY: ins.datemultirange_array_in,  # datemultirange[]
    oids.DATERANGE: ins.daterange_in,  # daterange
    oids.DATERANGE_ARRAY: ins.daterange_array_in,  # daterange[]
    oids.FLOAT: float,  # float8
    oids.FLOAT_ARRAY: ins.float_array_in,  # float8[]
    oids.INET: ins.inet_in,  # inet
    oids.INET_ARRAY: ins.inet_array_in,  # inet[]
    oids.INT4MULTIRANGE: ins.int4multirange_in,  # int4multirange
    oids.INT4MULTIRANGE_ARRAY: ins.int4multirange_array_in,  # int4multirange[]
    oids.INT4RANGE: ins.int4range_in,  # int4range
    oids.INT4RANGE_ARRAY: ins.int4range_array_in,  # int4range[]
    oids.INT8MULTIRANGE: ins.int8multirange_in,  # int8multirange
    oids.INT8MULTIRANGE_ARRAY: ins.int8multirange_array_in,  # int8multirange[]
    oids.INT8RANGE: ins.int8range_in,  # int8range
    oids.INT8RANGE_ARRAY: ins.int8range_array_in,  # int8range[]
    oids.INTEGER: int,  # int4
    oids.INTEGER_ARRAY: ins.int_array_in,  # int4[]
    oids.JSON: ins.json_in,  # json
    oids.JSON_ARRAY: ins.json_array_in,  # json[]
    oids.JSONB: ins.json_in,  # jsonb
    oids.JSONB_ARRAY: ins.json_array_in,  # jsonb[]
    oids.MACADDR: ins.string_in,  # MACADDR type
    oids.MONEY: ins.string_in,  # money
    oids.MONEY_ARRAY: ins.string_array_in,  # money[]
    oids.NAME: ins.string_in,  # name
    oids.NAME_ARRAY: ins.string_array_in,  # name[]
    oids.NUMERIC: ins.numeric_in,  # numeric
    oids.NUMERIC_ARRAY: ins.numeric_array_in,  # numeric[]
    oids.NUMRANGE: ins.numrange_in,  # numrange
    oids.NUMRANGE_ARRAY: ins.numrange_array_in,  # numrange[]
    oids.NUMMULTIRANGE: ins.nummultirange_in,  # nummultirange
    oids.NUMMULTIRANGE_ARRAY: ins.nummultirange_array_in,  # nummultirange[]
    oids.OID: int,  # oid
    oids.POINT: ins.point_in,  # point
    oids.INTERVAL: ins.interval_in,  # interval
    oids.INTERVAL_ARRAY: ins.interval_array_in,  # interval[]
    oids.REAL: float,  # float4
    oids.REAL_ARRAY: ins.float_array_in,  # float4[]
    oids.RECORD: ins.record_in,  # record
    oids.SMALLINT: int,  # int2
    oids.SMALLINT_ARRAY: ins.int_array_in,  # int2[]
    oids.SMALLINT_VECTOR: ins.vector_in,  # int2vector
    oids.TEXT: ins.string_in,  # text
    oids.TEXT_ARRAY: ins.string_array_in,  # text[]
    oids.TIME: ins.time_in,  # time
    oids.TIME_ARRAY: ins.time_array_in,  # time[]
    oids.TIMESTAMP: ins.timestamp_in,  # timestamp
    oids.TIMESTAMP_ARRAY: ins.timestamp_array_in,  # timestamp
    oids.TIMESTAMPTZ: ins.timestamptz_in,  # timestamptz
    oids.TIMESTAMPTZ_ARRAY: ins.timestamptz_array_in,  # timestamptz
    oids.TSMULTIRANGE: ins.tsmultirange_in,  # tsmultirange
    oids.TSMULTIRANGE_ARRAY: ins.tsmultirange_array_in,  # tsmultirange[]
    oids.TSRANGE: ins.tsrange_in,  # tsrange
    oids.TSRANGE_ARRAY: ins.tsrange_array_in,  # tsrange[]
    oids.TSTZMULTIRANGE: ins.tstzmultirange_in,  # tstzmultirange
    oids.TSTZMULTIRANGE_ARRAY: ins.tstzmultirange_array_in,  # tstzmultirange[]
    oids.TSTZRANGE: ins.tstzrange_in,  # tstzrange
    oids.TSTZRANGE_ARRAY: ins.tstzrange_array_in,  # tstzrange[]
    oids.UNKNOWN: ins.string_in,  # unknown
    oids.UUID_ARRAY: ins.uuid_array_in,  # uuid[]
    oids.UUID_TYPE: ins.uuid_in,  # uuid
    oids.VARCHAR: ins.string_in,  # varchar
    oids.VARCHAR_ARRAY: ins.string_array_in,  # varchar[]
    oids.XID: int,  # xid
}


def make_param(py_types: ta.Mapping[type, OutAdapter], value: ta.Any) -> str | None:
    func: OutAdapter
    try:
        func = py_types[type(value)]
    except KeyError:
        func = str
        for k, v in py_types.items():
            try:
                if isinstance(value, k):
                    func = v
                    break
            except TypeError:
                pass

    return func(value)


def make_params(py_types: ta.Mapping[type, OutAdapter], values: ta.Iterable[ta.Any]) -> tuple[str | None, ...]:
    return tuple([make_param(py_types, v) for v in values])


def identifier(sql: str) -> str:
    if not isinstance(sql, str):
        raise InterfaceError('identifier must be a str')

    if len(sql) == 0:
        raise InterfaceError('identifier must be > 0 characters in length')

    if '\u0000' in sql:
        raise InterfaceError('identifier cannot contain the code zero character')

    sql = sql.replace('"', '""')
    return f'"{sql}"'


@functools.singledispatch
def literal(value: ta.Any) -> str:
    val = str(value).replace("'", "''")
    return f"'{val}'"


@literal.register
def _(value: None) -> str:
    return 'NULL'


@literal.register
def _(value: bool) -> str:
    return 'TRUE' if value else 'FALSE'


@literal.register(int)
@literal.register(float)
@literal.register(decimal.Decimal)
def _(value: float | decimal.Decimal) -> str:
    return str(value)


@literal.register(bytes)
@literal.register(bytearray)
def _(value: bytes | bytearray) -> str:
    return f"X'{value.hex()}'"


@literal.register
def _(value: datetime.datetime) -> str:
    return f"'{datetime_out(value)}'"


@literal.register
def _(value: datetime.date) -> str:
    return f"'{date_out(value)}'"


@literal.register
def _(value: datetime.time) -> str:
    return f"'{time_out(value)}'"


@literal.register
def _(value: datetime.timedelta) -> str:
    return f"'{interval_out(value)}'"


@literal.register
def _(value: list) -> str:
    return f'{literal(array_out(value))}'
