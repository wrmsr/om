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
"""Input adapters: PostgreSQL text format to Python values."""

import datetime
import typing as ta
from decimal import Decimal
from enum import Enum
from ipaddress import ip_address
from ipaddress import ip_network
from json import loads
from uuid import UUID

from ..types import PGInterval
from ..types import Range
from .adapters import InAdapter
from .adapters import IpAddressOrNetwork


T = ta.TypeVar('T')



##


def bool_in(data: str) -> bool:
    return data == 't'


def bytes_in(data: str) -> bytes:
    return bytes.fromhex(data[2:])


def cidr_in(data: str) -> IpAddressOrNetwork:
    return ip_network(data, False) if '/' in data else ip_address(data)


def date_in(data: str) -> datetime.date | str:
    if data in ('infinity', '-infinity'):
        return data
    else:
        try:
            return datetime.datetime.strptime(data, '%Y-%m-%d').date()
        except ValueError:
            # pg date can overflow Python datetime.datetime
            return data


def inet_in(data: str) -> IpAddressOrNetwork:
    return ip_network(data, False) if '/' in data else ip_address(data)


def int_in(data: str) -> int:
    return int(data)


def interval_in(data: str) -> datetime.timedelta | PGInterval:
    pg_interval = PGInterval.from_str(data)
    try:
        return pg_interval.to_timedelta()
    except ValueError:
        return pg_interval


def json_in(data: str) -> ta.Any:
    return loads(data)


def numeric_in(data: str) -> Decimal:
    return Decimal(data)


def point_in(data: str) -> tuple[float, ...]:
    return tuple(map(float, data[1:-1].split(',')))


def pg_interval_in(data: str) -> PGInterval:
    return PGInterval.from_str(data)


def string_in(data: str) -> str:
    return data


def time_in(data: str) -> datetime.time:
    pattern = '%H:%M:%S.%f' if '.' in data else '%H:%M:%S'
    return datetime.datetime.strptime(data, pattern).time()


def timestamp_in(data: str) -> datetime.datetime | str:
    if data in ('infinity', '-infinity'):
        return data
    try:
        return datetime.datetime.fromisoformat(data)
    except ValueError:
        return data


def timestamptz_in(data: str) -> datetime.datetime | str:
    return timestamp_in(data)


def vector_in(data: str) -> list[int]:
    return [int(v) for v in data.split()]


def uuid_in(data: str) -> UUID:
    return UUID(data)


def _range_in(elem_func: ta.Callable[[str], T]) -> ta.Callable[[str], Range[T]]:
    def range_in(data: str) -> Range[T]:
        if data == 'empty':
            return Range(is_empty=True)
        else:
            le, ue = [None if v == '' else elem_func(v) for v in data[1:-1].split(',')]
            return Range(le, ue, bounds=f'{data[0]}{data[-1]}')

    return range_in


daterange_in = _range_in(date_in)


int4range_in = _range_in(int)


int8range_in = _range_in(int)


numrange_in = _range_in(Decimal)


def ts_in(data: str) -> datetime.datetime | str:
    return timestamp_in(data[1:-1])


def tstz_in(data: str) -> datetime.datetime | str:
    return timestamptz_in(data[1:-1])


tsrange_in = _range_in(ts_in)


tstzrange_in = _range_in(tstz_in)


def _multirange_in(adapter: ta.Callable[[str], T]) -> ta.Callable[[str], list[T]]:
    def f(data: str) -> list[T]:
        in_range = False
        result: list[T] = []
        val: list[str] = []
        for c in data:
            if in_range:
                val.append(c)
                if c in '])':
                    value = ''.join(val)
                    val.clear()
                    result.append(adapter(value))
                    in_range = False
            elif c in '[(':
                val.append(c)
                in_range = True

        return result

    return f


datemultirange_in = _multirange_in(daterange_in)


int4multirange_in = _multirange_in(int4range_in)


int8multirange_in = _multirange_in(int8range_in)


nummultirange_in = _multirange_in(numrange_in)


tsmultirange_in = _multirange_in(tsrange_in)


tstzmultirange_in = _multirange_in(tstzrange_in)


class ParserState(Enum):
    InString = 1
    InEscape = 2
    InValue = 3
    Out = 4


def _parse_array(data: str, adapter: InAdapter) -> list[ta.Any]:
    state = ParserState.Out
    stack: list[list[ta.Any]] = [[]]
    val: list[str] = []
    for c in data:
        if state == ParserState.InValue:
            if c in ('}', ','):
                value = ''.join(val)
                stack[-1].append(None if value == 'NULL' else adapter(value))
                state = ParserState.Out
            else:
                val.append(c)

        if state == ParserState.Out:
            if c == '{':
                a: list[ta.Any] = []
                stack[-1].append(a)
                stack.append(a)
            elif c == '}':
                stack.pop()
            elif c == ',':
                pass
            elif c == '"':
                val = []
                state = ParserState.InString
            else:
                val = [c]
                state = ParserState.InValue

        elif state == ParserState.InString:
            if c == '"':
                stack[-1].append(adapter(''.join(val)))
                state = ParserState.Out
            elif c == '\\':
                state = ParserState.InEscape
            else:
                val.append(c)
        elif state == ParserState.InEscape:
            val.append(c)
            state = ParserState.InString

    return stack[0][0]


def _array_in(adapter: InAdapter) -> ta.Callable[[str], list[ta.Any]]:
    def f(data: str) -> list[ta.Any]:
        return _parse_array(data, adapter)

    return f


bool_array_in = _array_in(bool_in)


bytes_array_in = _array_in(bytes_in)


cidr_array_in = _array_in(cidr_in)


date_array_in = _array_in(date_in)


datemultirange_array_in = _array_in(datemultirange_in)


daterange_array_in = _array_in(daterange_in)


inet_array_in = _array_in(inet_in)


int_array_in = _array_in(int)


int4multirange_array_in = _array_in(int4multirange_in)


int4range_array_in = _array_in(int4range_in)


int8multirange_array_in = _array_in(int8multirange_in)


int8range_array_in = _array_in(int8range_in)


interval_array_in = _array_in(interval_in)


json_array_in = _array_in(json_in)


float_array_in = _array_in(float)


numeric_array_in = _array_in(numeric_in)


nummultirange_array_in = _array_in(nummultirange_in)


numrange_array_in = _array_in(numrange_in)


string_array_in = _array_in(string_in)


time_array_in = _array_in(time_in)


timestamp_array_in = _array_in(timestamp_in)


timestamptz_array_in = _array_in(timestamptz_in)


tsrange_array_in = _array_in(tsrange_in)


tsmultirange_array_in = _array_in(tsmultirange_in)


tstzmultirange_array_in = _array_in(tstzmultirange_in)


tstzrange_array_in = _array_in(tstzrange_in)


uuid_array_in = _array_in(uuid_in)


def record_in(data: str) -> tuple[str | None, ...]:
    state = ParserState.Out
    results: list[str | None] = []
    val: list[str] = []
    for c in data:
        if state == ParserState.InValue:
            if c in (')', ','):
                value = ''.join(val)
                val.clear()
                results.append(None if value == '' else value)
                state = ParserState.Out
            else:
                val.append(c)

        if state == ParserState.Out:
            if c in '(),':
                pass
            elif c == '"':
                state = ParserState.InString
            else:
                val.append(c)
                state = ParserState.InValue

        elif state == ParserState.InString:
            if c == '"':
                results.append(''.join(val))
                val.clear()
                state = ParserState.Out
            elif c == '\\':
                state = ParserState.InEscape
            else:
                val.append(c)

        elif state == ParserState.InEscape:
            val.append(c)
            state = ParserState.InString

    return tuple(results)
