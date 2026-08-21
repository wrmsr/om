"""
Typed representations of PostgreSQL protocol messages. These are pure data: encoding and decoding live in the sibling
`encoding` and `decoding` modules, and no message knows anything about IO.
"""
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from .codes import DescribeKind
from .codes import TransactionStatus


##


class BackendMessage(lang.Abstract):
    pass


class FrontendMessage(lang.Abstract):
    pass


##
# Authentication


class Authentication(BackendMessage, lang.Abstract):
    pass


@dc.dataclass(frozen=True)
class AuthenticationOk(Authentication):
    pass


@dc.dataclass(frozen=True)
class AuthenticationCleartextPassword(Authentication):
    pass


@dc.dataclass(frozen=True)
class AuthenticationMd5Password(Authentication):
    salt: bytes


@dc.dataclass(frozen=True)
class AuthenticationSasl(Authentication):
    mechanisms: ta.Sequence[str]


@dc.dataclass(frozen=True)
class AuthenticationSaslContinue(Authentication):
    data: bytes


@dc.dataclass(frozen=True)
class AuthenticationSaslFinal(Authentication):
    data: bytes


@dc.dataclass(frozen=True)
class AuthenticationOther(Authentication):
    """An authentication request of a kind this client does not implement."""

    code: int
    data: bytes


##
# Other backend messages


@dc.dataclass(frozen=True)
class BackendKeyData(BackendMessage):
    process_id: int
    secret_key: int


@dc.dataclass(frozen=True)
class ParameterStatus(BackendMessage):
    name: str
    value: str


@dc.dataclass(frozen=True)
class ReadyForQuery(BackendMessage):
    status: TransactionStatus


@dc.dataclass(frozen=True)
class FieldDescription:
    name: str
    table_oid: int
    column_attrnum: int
    type_oid: int
    type_size: int
    type_modifier: int
    format_code: int


@dc.dataclass(frozen=True)
class RowDescription(BackendMessage):
    fields: ta.Sequence[FieldDescription]


@dc.dataclass(frozen=True)
class DataRow(BackendMessage):
    values: ta.Sequence[bytes | None]


@dc.dataclass(frozen=True)
class CommandComplete(BackendMessage):
    tag: str


@dc.dataclass(frozen=True)
class ErrorResponse(BackendMessage):
    fields: ta.Mapping[str, str]


@dc.dataclass(frozen=True)
class NoticeResponse(BackendMessage):
    fields: ta.Mapping[str, str]


@dc.dataclass(frozen=True)
class NotificationResponse(BackendMessage):
    process_id: int
    channel: str
    payload: str


@dc.dataclass(frozen=True)
class ParameterDescription(BackendMessage):
    type_oids: ta.Sequence[int]


@dc.dataclass(frozen=True)
class ParseComplete(BackendMessage):
    pass


@dc.dataclass(frozen=True)
class BindComplete(BackendMessage):
    pass


@dc.dataclass(frozen=True)
class CloseComplete(BackendMessage):
    pass


@dc.dataclass(frozen=True)
class PortalSuspended(BackendMessage):
    pass


@dc.dataclass(frozen=True)
class NoData(BackendMessage):
    pass


@dc.dataclass(frozen=True)
class EmptyQueryResponse(BackendMessage):
    pass


@dc.dataclass(frozen=True)
class CopyInResponse(BackendMessage):
    is_binary: bool
    column_formats: ta.Sequence[int]


@dc.dataclass(frozen=True)
class CopyOutResponse(BackendMessage):
    is_binary: bool
    column_formats: ta.Sequence[int]


##
# Messages flowing in both directions


@dc.dataclass(frozen=True)
class CopyData(BackendMessage, FrontendMessage):
    data: bytes


@dc.dataclass(frozen=True)
class CopyDone(BackendMessage, FrontendMessage):
    pass


##
# SSL negotiation


@dc.dataclass(frozen=True)
class SslRequest(FrontendMessage):
    pass


@dc.dataclass(frozen=True)
class SslResponse(BackendMessage):
    """
    The single byte reply to an SslRequest. This is not a framed message, so it is produced by transport framing rather
    than the message decoder.
    """

    accepted: bool


##
# Frontend messages


@dc.dataclass(frozen=True)
class StartupMessage(FrontendMessage):
    params: ta.Mapping[str, bytes]


@dc.dataclass(frozen=True)
class PasswordMessage(FrontendMessage):
    password: bytes


@dc.dataclass(frozen=True)
class SaslInitialResponse(FrontendMessage):
    mechanism: str
    data: bytes


@dc.dataclass(frozen=True)
class SaslResponse(FrontendMessage):
    data: bytes


@dc.dataclass(frozen=True)
class Query(FrontendMessage):
    sql: str


@dc.dataclass(frozen=True)
class Parse(FrontendMessage):
    name: str
    sql: str
    type_oids: ta.Sequence[int] = ()


@dc.dataclass(frozen=True)
class Bind(FrontendMessage):
    portal: str
    statement: str
    params: ta.Sequence[str | None] = ()


@dc.dataclass(frozen=True)
class Describe(FrontendMessage):
    kind: DescribeKind
    name: str


@dc.dataclass(frozen=True)
class Execute(FrontendMessage):
    portal: str
    max_rows: int = 0


@dc.dataclass(frozen=True)
class Close(FrontendMessage):
    kind: DescribeKind
    name: str


@dc.dataclass(frozen=True)
class Flush(FrontendMessage):
    pass


@dc.dataclass(frozen=True)
class Sync(FrontendMessage):
    pass


@dc.dataclass(frozen=True)
class Terminate(FrontendMessage):
    pass


@dc.dataclass(frozen=True)
class CopyFail(FrontendMessage):
    message: str
