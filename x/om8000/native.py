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
import collections
import enum

from .converters import BIGINT
from .converters import BOOLEAN
from .converters import BOOLEAN_ARRAY
from .converters import BYTES
from .converters import CHAR
from .converters import CHAR_ARRAY
from .converters import DATE
from .converters import FLOAT
from .converters import FLOAT_ARRAY
from .converters import INET
from .converters import INT2VECTOR
from .converters import INTEGER
from .converters import INTEGER_ARRAY
from .converters import INTERVAL
from .converters import JSON
from .converters import JSON_ARRAY
from .converters import JSONB
from .converters import JSONB_ARRAY
from .converters import MACADDR
from .converters import NAME
from .converters import NAME_ARRAY
from .converters import NULLTYPE
from .converters import NUMERIC
from .converters import NUMERIC_ARRAY
from .converters import OID
from .converters import STRING
from .converters import TEXT
from .converters import TEXT_ARRAY
from .converters import TIME
from .converters import TIMESTAMP
from .converters import TIMESTAMPTZ
from .converters import UNKNOWN
from .converters import UUID_TYPE
from .converters import VARCHAR
from .converters import VARCHAR_ARRAY
from .converters import XID
from .converters import PGInterval
from .converters import identifier
from .converters import literal
from .converters import make_params
from .core import CoreConnection
from .exceptions import DatabaseError
from .exceptions import Error
from .exceptions import InterfaceError
from .types import Range


##


class State(enum.Enum):
    OUT = enum.auto()  # outside quoted string
    IN_SQ = enum.auto()  # inside single-quote string '...'
    IN_QI = enum.auto()  # inside quoted identifier   "..."
    IN_ES = enum.auto()  # inside escaped single-quote string, E'...'
    IN_PN = enum.auto()  # inside parameter name eg. :name
    IN_CO = enum.auto()  # inside inline comment eg. --
    IN_DQ = enum.auto()  # inside dollar-quoted string eg. $$...$$
    IN_DP = enum.auto()  # inside dollar parameter eg. $1


def to_statement(query):
    in_quote_escape = False
    placeholders = []
    output_query = []
    state = State.OUT
    prev_c = None
    for i, c in enumerate(query):
        if i + 1 < len(query):
            next_c = query[i + 1]
        else:
            next_c = None

        if state == State.OUT:
            if c == "'":
                output_query.append(c)
                if prev_c == 'E':
                    state = State.IN_ES
                else:
                    state = State.IN_SQ

            elif c == '"':
                output_query.append(c)
                state = State.IN_QI

            elif c == '-':
                output_query.append(c)
                if prev_c == '-':
                    state = State.IN_CO

            elif c == '$':
                output_query.append(c)
                if prev_c == '$':
                    state = State.IN_DQ
                elif next_c.isdigit():
                    state = State.IN_DP
                    placeholders.append('')

            elif c == ':' and next_c not in ':=' and prev_c != ':':
                state = State.IN_PN
                placeholders.append('')

            else:
                output_query.append(c)

        elif state == State.IN_SQ:
            if c == "'":
                if in_quote_escape:
                    in_quote_escape = False
                elif next_c == "'":
                    in_quote_escape = True
                else:
                    state = State.OUT
            output_query.append(c)

        elif state == State.IN_QI:
            if c == '"':
                state = State.OUT
            output_query.append(c)

        elif state == State.IN_ES:
            if c == "'" and prev_c != '\\':
                # check for escaped single-quote
                state = State.OUT
            output_query.append(c)

        elif state == State.IN_PN:
            placeholders[-1] += c
            if next_c is None or (not next_c.isalnum() and next_c != '_'):
                state = State.OUT
                try:
                    pidx = placeholders.index(placeholders[-1], 0, -1)
                    output_query.append(f'${pidx + 1}')
                    del placeholders[-1]
                except ValueError:
                    output_query.append(f'${len(placeholders)}')

        elif state == State.IN_DP:
            placeholders[-1] += c
            output_query.append(c)
            if next_c is None or not next_c.isdigit():
                try:
                    placeholders[-1] = int(placeholders[-1]) - 1
                except ValueError:
                    raise InterfaceError(f"Expected an integer for the $ placeholder but found '{placeholders[-1]}'")
                state = State.OUT

        elif state == State.IN_CO:
            output_query.append(c)
            if c == '\n':
                state = State.OUT

        elif state == State.IN_DQ:
            output_query.append(c)
            if c == '$' and prev_c == '$':
                state = State.OUT

        prev_c = c

    for reserved in ('types', 'stream'):
        if reserved in placeholders:
            raise InterfaceError(
                f"The name '{reserved}' can't be used as a placeholder because it's "
                f"used for another purpose.",
            )

    def make_vals(args):
        arg_list = [v for _, v in args.items()]
        vals = []
        for p in placeholders:
            if isinstance(p, int):
                vals.append(arg_list[p])
            else:
                try:
                    vals.append(args[p])
                except KeyError:
                    raise InterfaceError(f"There's a placeholder '{p}' in the query, but no matching keyword argument.")
        return tuple(vals)

    return ''.join(output_query), make_vals


class Connection(CoreConnection):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self._context = None

    @property
    def columns(self):
        context = self._context
        if context is None:
            return None
        return context.columns

    @property
    def row_count(self):
        context = self._context
        if context is None:
            return None
        return context.row_count

    def run(self, sql, stream=None, types=None, **params):
        if len(params) == 0 and stream is None:
            self._context = self.execute_simple(sql)
        else:
            statement, make_vals = to_statement(sql)
            oids = () if types is None else make_vals(collections.defaultdict(lambda: None, types))
            self._context = self.execute_unnamed(
                statement,
                make_vals(params),
                oids=oids,
                stream=stream,
            )
        return self._context.rows

    def prepare(self, sql):
        return PreparedStatement(self, sql)


class PreparedStatement:
    def __init__(self, con, sql, types=None):
        self.con = con
        self.statement, self.make_vals = to_statement(sql)
        oids = () if types is None else self.make_vals(collections.defaultdict(lambda: None, types))
        self.name_bin, self.cols, self.input_funcs = con.prepare_statement(self.statement, oids)

    @property
    def columns(self):
        return self._context.columns

    def run(self, stream=None, **params):
        params = make_params(self.con.py_types, self.make_vals(params))

        self._context = self.con.execute_named(
            self.name_bin,
            params,
            self.cols,
            self.input_funcs,
            self.statement,
        )

        return self._context.rows

    def close(self):
        self.con.close_prepared_statement(self.name_bin)
