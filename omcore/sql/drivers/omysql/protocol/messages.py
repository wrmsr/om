# Copyright (c) 2010, 2013 PyMySQL contributors
#
# Permission is hereby granted, free of charge, to any person obtaining a copy of this software and associated
# documentation files (the "Software"), to deal in the Software without restriction, including without limitation the
# rights to use, copy, modify, merge, publish, distribute, sublicense, and/or sell copies of the Software, and to permit
# persons to whom the Software is furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in all copies or substantial portions of the
# Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR IMPLIED, INCLUDING BUT NOT LIMITED TO THE
# WARRANTIES OF MERCHANTABILITY, FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE AUTHORS OR
# COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR
# OTHERWISE, ARISING FROM, OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN THE SOFTWARE.
"""Typed representations of the server's packets. These are pure data: parsing lives in the sibling `parsing` module."""
import typing as ta

from ..... import dataclasses as dc
from ..charset import MBLENGTH
from ..constants import FIELD_TYPE
from ..constants import SERVER_STATUS


##


@dc.dataclass(frozen=True)
class Handshake:
    """The server's initial greeting (Protocol::HandshakeV10)."""

    protocol_version: int
    server_version: str
    thread_id: int
    auth_plugin_data: bytes
    capabilities: int
    charset_id: int | None
    status_flags: int
    auth_plugin_name: str


@dc.dataclass(frozen=True)
class OkPacket:
    affected_rows: int
    insert_id: int
    status_flags: int
    warning_count: int
    message: bytes

    @property
    def has_next(self) -> bool:
        return bool(self.status_flags & SERVER_STATUS.SERVER_MORE_RESULTS_EXISTS)


@dc.dataclass(frozen=True)
class EofPacket:
    warning_count: int
    status_flags: int

    @property
    def has_next(self) -> bool:
        return bool(self.status_flags & SERVER_STATUS.SERVER_MORE_RESULTS_EXISTS)


@dc.dataclass(frozen=True)
class ErrPacket:
    errno: int
    sqlstate: str | None
    message: str


@dc.dataclass(frozen=True)
class AuthSwitchRequest:
    plugin_name: str
    data: bytes


@dc.dataclass(frozen=True)
class AuthMoreData:
    data: bytes


@dc.dataclass(frozen=True)
class LocalInfileRequest:
    filename: bytes


@dc.dataclass(frozen=True)
class ColumnDefinition:
    catalog: bytes
    db: bytes
    table_name: str
    org_table: str
    name: str
    org_name: str
    charsetnr: int
    length: int
    type_code: int
    flags: int
    scale: int

    @property
    def column_length(self) -> int:
        if self.type_code == FIELD_TYPE.VAR_STRING:
            return self.length // MBLENGTH.get(self.charsetnr, 1)
        return self.length

    def description(self) -> tuple[ta.Any, ...]:
        """The PEP 249 seven item description of this column."""

        return (
            self.name,
            self.type_code,
            None,  # display_size
            self.column_length,  # internal_size
            self.column_length,  # precision
            self.scale,
            self.flags % 2 == 0,  # null_ok
        )
