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
"""Output adapters: Python values to PostgreSQL text format."""

import datetime
import decimal
import enum
import json
import typing as ta
import uuid

from ..types import PGInterval
from .adapters import IpAddressOrNetwork


##


def bool_out(v: bool) -> str:
    return 'true' if v else 'false'


def bytes_out(v: bytes | bytearray) -> str:
    return '\\x' + v.hex()


def cidr_out(v: IpAddressOrNetwork) -> str:
    return str(v)


def date_out(v: datetime.date) -> str:
    return v.isoformat()


def datetime_out(v: datetime.datetime) -> str:
    if v.tzinfo is None:
        return v.isoformat()
    else:
        return v.astimezone(datetime.UTC).isoformat()


def enum_out(v: enum.Enum) -> str:
    return str(v.value)


def float_out(v: float) -> str:
    return str(v)


def inet_out(v: IpAddressOrNetwork) -> str:
    return str(v)


def int_out(v: int) -> str:
    return str(v)


def interval_out(v: datetime.timedelta) -> str:
    return f'{v.days} days {v.seconds} seconds {v.microseconds} microseconds'


def json_out(v: ta.Any) -> str:
    return json.dumps(v)


def null_out(v: None) -> None:
    return None


def numeric_out(d: decimal.Decimal) -> str:
    return str(d)


def pg_interval_out(v: PGInterval) -> str:
    return str(v)


def string_out(v: str) -> str:
    return v


def time_out(v: datetime.time) -> str:
    return v.isoformat()


def unknown_out(v: ta.Any) -> str:
    return str(v)


def uuid_out(v: uuid.UUID) -> str:
    return str(v)


def array_string_escape(v: str) -> str:
    cs: list[str] = []
    for c in v:
        if c == '\\':
            cs.append('\\')
        elif c == '"':
            cs.append('\\')
        cs.append(c)
    val = ''.join(cs)
    if (
        len(val) == 0
        or val == 'NULL'
        or any(c.isspace() for c in val)
        or any(c in val for c in ('{', '}', ',', '\\'))
    ):
        val = f'"{val}"'
    return val
