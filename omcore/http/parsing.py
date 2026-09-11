# ruff: noqa: UP006 UP007 UP045
# @om-lite
"""
Parses a complete HTTP/1.x start-line + header fields + final CRLF from a ``bytes`` object. Does NOT handle message
bodies, chunked transfer decoding, or HTTP/2+.

TODO:
 - mapping from error code to outbound http status code
"""
import dataclasses as dc
import datetime
import enum
import io
import re
import typing as ta

from ..lite.bytes import Bytes
from .versions import HttpVersion
from .versions import HttpVersions


##


class StartLineHttpParseErrorCode(enum.Enum):
    MALFORMED_REQUEST_LINE = enum.auto()
    MALFORMED_STATUS_LINE = enum.auto()
    UNSUPPORTED_HTTP_VERSION = enum.auto()
    INVALID_METHOD = enum.auto()
    INVALID_REQUEST_TARGET = enum.auto()
    INVALID_STATUS_CODE = enum.auto()


class HeaderFieldHttpParseErrorCode(enum.Enum):
    INVALID_FIELD_NAME = enum.auto()
    INVALID_FIELD_VALUE = enum.auto()
    OBS_FOLD_NOT_ALLOWED = enum.auto()
    SPACE_BEFORE_COLON = enum.auto()
    MISSING_COLON = enum.auto()
    BARE_CARRIAGE_RETURN = enum.auto()
    BARE_LF = enum.auto()
    NUL_IN_HEADER = enum.auto()
    MISSING_TERMINATOR = enum.auto()
    TRAILING_DATA = enum.auto()
    TOO_MANY_HEADERS = enum.auto()
    EMPTY_FIELD_NAME = enum.auto()


class SemanticHeaderHttpParseErrorCode(enum.Enum):
    DUPLICATE_CONTENT_LENGTH = enum.auto()
    CONFLICTING_CONTENT_LENGTH = enum.auto()
    CONTENT_LENGTH_WITH_TRANSFER_ENCODING = enum.auto()
    MISSING_HOST_HEADER = enum.auto()
    MULTIPLE_HOST_HEADERS = enum.auto()
    CONFLICTING_HOST_HEADERS = enum.auto()
    INVALID_CONTENT_LENGTH = enum.auto()
    INVALID_TRANSFER_ENCODING = enum.auto()
    INVALID_CONTENT_TYPE = enum.auto()
    FORBIDDEN_TRAILER_FIELD = enum.auto()
    INVALID_HOST = enum.auto()
    INVALID_EXPECT = enum.auto()
    INVALID_DATE = enum.auto()
    INVALID_CACHE_CONTROL = enum.auto()
    INVALID_ACCEPT_ENCODING = enum.auto()
    INVALID_ACCEPT = enum.auto()
    INVALID_AUTHORIZATION = enum.auto()
    TE_WITHOUT_CHUNKED_LAST = enum.auto()
    INVALID_TE = enum.auto()

    # The Transfer-Encoding header (not the TE header) in an HTTP/1.0 message.
    TRANSFER_ENCODING_IN_HTTP10 = enum.auto()

    # Deprecated alias for TRANSFER_ENCODING_IN_HTTP10 - retained for backwards compatibility. The old name was
    # ambiguous: it referred to the Transfer-Encoding header, not the TE header.
    TE_IN_HTTP10 = TRANSFER_ENCODING_IN_HTTP10

    # The TE header (not the Transfer-Encoding header) in an HTTP/1.0 message.
    TE_HEADER_IN_HTTP10 = enum.auto()

    # The TE header grants 'trailers' with a zero qvalue, which must not be accepted (RFC 7230 §4.3).
    TE_TRAILERS_Q_ZERO = enum.auto()

    MULTIPLE_CONTENT_TYPES = enum.auto()
    CONFLICTING_CONTENT_TYPES = enum.auto()
    MULTIPLE_AUTHORIZATION_HEADERS = enum.auto()
    UPGRADE_WITHOUT_CONNECTION_UPGRADE = enum.auto()

    # A Connection header option or Trailer header field-name that is not a valid token.
    INVALID_CONNECTION = enum.auto()
    INVALID_TRAILER_FIELD = enum.auto()

    # An Upgrade protocol, or protocol "/" version, that is not a valid token (RFC 7230 §6.7).
    INVALID_UPGRADE = enum.auto()

    # The Upgrade header in an HTTP/1.0 request (RFC 7230 §6.7).
    UPGRADE_IN_HTTP10 = enum.auto()

    # Request-only header fields present in a response message.
    HOST_IN_RESPONSE = enum.auto()
    TE_IN_RESPONSE = enum.auto()
    EXPECT_IN_RESPONSE = enum.auto()


class EncodingHttpParseErrorCode(enum.Enum):
    NON_ASCII_IN_FIELD_NAME = enum.auto()
    OBS_TEXT_IN_FIELD_VALUE = enum.auto()


HttpParseErrorCode = ta.Union[  # ta.TypeAlias  # om-amalg-typing-no-move
    StartLineHttpParseErrorCode,
    HeaderFieldHttpParseErrorCode,
    SemanticHeaderHttpParseErrorCode,
    EncodingHttpParseErrorCode,
]


##


class HttpParseError(Exception):
    pass


@dc.dataclass()
class ErrorCodeHttpParseError(HttpParseError):
    """Base exception for all HTTP header parsing errors."""

    code: HttpParseErrorCode
    message: str = ''
    line: int = 0
    offset: int = 0

    def __post_init__(self) -> None:
        Exception.__init__(self, str(self))

    def __str__(self) -> str:
        return f'[{self.code.name}] line {self.line}, offset {self.offset}: {self.message}'


@dc.dataclass()
class StartLineHttpParseError(ErrorCodeHttpParseError):
    """Errors in the request-line or status-line."""

    code: StartLineHttpParseErrorCode = dc.field(default=StartLineHttpParseErrorCode.MALFORMED_REQUEST_LINE)


@dc.dataclass()
class HeaderFieldHttpParseError(ErrorCodeHttpParseError):
    """Errors in header field syntax."""

    code: HeaderFieldHttpParseErrorCode = dc.field(default=HeaderFieldHttpParseErrorCode.INVALID_FIELD_NAME)


@dc.dataclass()
class SemanticHeaderHttpParseError(ErrorCodeHttpParseError):
    """Errors in header field semantics / cross-field validation."""

    code: SemanticHeaderHttpParseErrorCode = dc.field(default=SemanticHeaderHttpParseErrorCode.INVALID_CONTENT_LENGTH)


@dc.dataclass()
class EncodingHttpParseError(ErrorCodeHttpParseError):
    """Errors in character encoding within headers."""

    code: EncodingHttpParseErrorCode = dc.field(default=EncodingHttpParseErrorCode.NON_ASCII_IN_FIELD_NAME)


@dc.dataclass()
class NoCombineHeaderHttpParseError(HttpParseError):
    """Errors in headers where duplicate values are not allowed."""

    name: str


##


@ta.final
class ParsedHttpHeaders:
    """
    Normalized, case-insensitive header mapping.

    Field names are stored in lowercase. Values are decoded as Latin-1. Multiple values for the same field-name are
    stored individually and combined with ``", "`` on access (except Set-Cookie, which is never combined).
    """

    def __init__(self) -> None:
        # normalized name -> list of individual values
        self._entries: ta.Dict[str, ta.List[str]] = {}

        # insertion-ordered unique names
        self._order: ta.List[str] = []

    def _add(self, name: str, value: str) -> None:
        if name not in self._entries:
            self._entries[name] = []
            self._order.append(name)
        self._entries[name].append(value)

    @property
    def entries(self) -> ta.Mapping[str, ta.Sequence[str]]:
        # Defensive copies: the internal lists and dict are mutable private state - handing them out would let callers
        # desync _entries from _order (which breaks items() with a KeyError).
        return {name: list(values) for name, values in self._entries.items()}

    def __contains__(self, name: ta.Any) -> bool:
        if not isinstance(name, str):
            return False
        return name.lower() in self._entries

    # Headers where duplicate values are comma-combined per RFC 7230 §3.2.2. Set-Cookie is the notable exception.
    _NO_COMBINE_HEADERS: ta.ClassVar[ta.FrozenSet[str]] = frozenset({
        'set-cookie',
    })

    def __getitem__(self, name: str) -> str:
        if not isinstance(name, str):
            raise TypeError(name)

        key = name.lower()
        values = self._entries[key]
        if key in self._NO_COMBINE_HEADERS:
            raise NoCombineHeaderHttpParseError(name)
        return ', '.join(values)

    def get(self, name: str, default: ta.Optional[str] = None) -> ta.Optional[str]:
        if not isinstance(name, str):
            raise TypeError(name)

        key = name.lower()
        values = self._entries.get(key)
        if not values:
            return default

        # Never raise NoCombineHeaderHttpParseError from get(): for a no-combine header return the first value (use
        # get_all() for the rest) rather than a corrupt comma-joined string.
        if key in self._NO_COMBINE_HEADERS:
            return values[0]

        return ', '.join(values)

    def get_all(self, name: str) -> ta.List[str]:
        if not isinstance(name, str):
            raise TypeError(name)

        return list(self._entries.get(name.lower(), []))

    def items(self) -> ta.List[ta.Tuple[str, str]]:
        result: ta.List[ta.Tuple[str, str]] = []
        for name in self._order:
            values = self._entries[name]
            if name in self._NO_COMBINE_HEADERS:
                for v in values:
                    result.append((name, v))
            else:
                result.append((name, ', '.join(values)))
        return result

    def keys(self) -> ta.List[str]:
        return list(self._order)

    def __iter__(self) -> ta.Iterator[str]:
        return iter(self._order)

    def __len__(self) -> int:
        return len(self._order)

    def __repr__(self) -> str:
        # items(), not dict(...): dict() would collapse multiple Set-Cookie (or any no-combine) values to the last
        # one - the repr must show what was actually received.
        return f'{self.__class__.__name__}({self.items()!r})'


@dc.dataclass()
class PreparedParsedHttpHeaders:
    content_length: ta.Optional[int] = None

    transfer_encoding: ta.Optional[ta.List[str]] = None

    host: ta.Optional[str] = None

    connection: ta.Optional[ta.FrozenSet[str]] = None
    keep_alive: ta.Optional[bool] = None

    @dc.dataclass(frozen=True)
    class ContentType:
        media_type: str
        params: ta.Dict[str, str]

        @property
        def charset(self) -> ta.Optional[str]:
            return self.params.get('charset')

    content_type: ta.Optional[ContentType] = None

    te: ta.Optional[ta.List[str]] = None

    upgrade: ta.Optional[ta.List[str]] = None

    trailer: ta.Optional[ta.FrozenSet[str]] = None

    expect: ta.Optional[str] = None
    expect_100_continue: ta.Optional[bool] = None

    date: ta.Optional[datetime.datetime] = None

    cache_control: ta.Optional[ta.Dict[str, ta.Optional[str]]] = None

    @dc.dataclass(frozen=True)
    class AcceptEncodingItem:
        coding: str
        q: float = 1.0

    accept_encoding: ta.Optional[ta.List[AcceptEncodingItem]] = None

    @dc.dataclass(frozen=True)
    class AcceptItem:
        media_range: str
        q: float = 1.0
        params: ta.Dict[str, str] = dc.field(default_factory=dict)

    accept: ta.Optional[ta.List[AcceptItem]] = None

    @dc.dataclass(frozen=True)
    class AuthorizationValue:
        scheme: str
        credentials: str

    authorization: ta.Optional[AuthorizationValue] = None

    def __repr__(self) -> str:
        return ''.join([
            f'{self.__class__.__name__}(',
            ', '.join([
                f'{f.name}={v!r}'
                for f in dc.fields(self)
                if (v := getattr(self, f.name)) is not None
            ]),
            ')',
        ])


@dc.dataclass(frozen=True)
class RawParsedHttpHeader:
    name: Bytes
    value: Bytes

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({self.name!r}, {self.value!r})'


@dc.dataclass()
class ParsedHttpMessage:
    class Kind(enum.Enum):
        REQUEST = 'request'
        RESPONSE = 'response'

    kind: Kind

    @dc.dataclass(frozen=True)
    class RequestLine:
        method: str
        request_target: Bytes
        http_version: HttpVersion

    request_line: ta.Optional[RequestLine]

    @dc.dataclass(frozen=True)
    class StatusLine:
        http_version: HttpVersion
        status_code: int
        reason_phrase: str

    status_line: ta.Optional[StatusLine]

    raw_headers: ta.List[RawParsedHttpHeader]
    headers: ParsedHttpHeaders

    prepared: PreparedParsedHttpHeaders


@dc.dataclass(frozen=True)
class ParsedHttpTrailers:
    """Result of parsing HTTP trailer fields."""

    raw_headers: ta.List[RawParsedHttpHeader]
    headers: ParsedHttpHeaders


##


class HttpParser:
    """Strict HTTP/1.x parser."""

    @dc.dataclass(frozen=True)
    class Config:
        """Strictness knobs. Defaults are maximally strict."""

        allow_obs_fold: bool = False
        dangerous_allow_space_before_colon: bool = False  # DANGEROUS - upstreams may not handle well
        allow_multiple_content_lengths: bool = False
        allow_content_length_with_te: bool = False
        allow_bare_lf: bool = False
        allow_missing_host: bool = False
        allow_multiple_hosts: bool = False
        allow_unknown_transfer_encoding: bool = False
        reject_empty_header_values: bool = False
        allow_bare_cr_in_value: bool = False
        allow_te_without_chunked_in_response: bool = False
        allow_transfer_encoding_http10: bool = False
        allow_te_header_http10: bool = False
        allow_multiple_content_types: bool = False
        allow_upgrade_without_connection_upgrade: bool = False
        reject_multi_value_content_length: bool = False
        reject_obs_text: bool = False
        reject_non_visible_ascii_request_target: bool = False
        max_header_count: int = 128
        max_header_length: ta.Optional[int] = 8192
        max_content_length_str_len: ta.Optional[int] = 20

    def __init__(self, config: Config = Config()) -> None:
        super().__init__()

        if not isinstance(config, HttpParser.Config):
            raise TypeError(f'Expected HttpParser.Config, got {type(config).__name__}')

        self._config = config

    # Public API

    class Mode(enum.Enum):
        REQUEST = 'request'
        RESPONSE = 'response'
        AUTO = 'auto'

    def parse_message(self, data: Bytes, mode: Mode = Mode.AUTO) -> ParsedHttpMessage:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError(f'Expected bytes, got {type(data).__name__}')

        if not isinstance(mode, HttpParser.Mode):
            raise TypeError(f'Expected HttpParser.Mode, got {type(mode).__name__}')

        ctx = _HttpParseContext(
            data=bytes(data),
            config=self._config,
            mode=mode,
        )

        # 1. Verify terminator
        ctx.verify_terminator()

        # 2. Split off start-line (slice ctx.data, the normalized bytes copy, so downstream fields like request_target
        # are always bytes even when the caller passed a bytearray)
        start_line_end = ctx.find_line_end(0)
        start_line_bytes = ctx.data[:start_line_end]

        # 3. Determine message kind
        kind = ctx.detect_kind(start_line_bytes)

        # 4. Parse start-line
        request_line: ta.Optional[ParsedHttpMessage.RequestLine] = None
        status_line: ta.Optional[ParsedHttpMessage.StatusLine] = None
        if kind == ParsedHttpMessage.Kind.REQUEST:
            request_line = ctx.parse_request_line(start_line_bytes)
        else:
            status_line = ctx.parse_status_line(start_line_bytes)

        http_version = (
            request_line.http_version if request_line else
            status_line.http_version if status_line else
            HttpVersions.HTTP_1_1
        )

        # 5. Parse header fields
        # Position after start-line CRLF (or LF if bare LF allowed)
        header_start = start_line_end + ctx.line_ending_len(start_line_end)
        raw_headers = ctx.parse_header_fields(header_start)

        # 6. Build normalized headers
        headers = ParsedHttpHeaders()
        for rh in raw_headers:
            name_str = rh.name.decode('ascii').lower()
            value_str = rh.value.decode('latin-1')
            headers._add(name_str, value_str)  # noqa

        # 7. Build prepared headers
        prepared = ctx.prepare_headers(headers, kind, http_version)

        return ParsedHttpMessage(
            kind=kind,
            request_line=request_line,
            status_line=status_line,
            raw_headers=raw_headers,
            headers=headers,
            prepared=prepared,
        )

    def parse_trailers(
        self,
        data: Bytes,
    ) -> ParsedHttpTrailers:
        if not isinstance(data, (bytes, bytearray)):
            raise TypeError(f'Expected bytes, got {type(data).__name__}')

        # Special case: empty trailers (just the terminating empty line, no fields)
        if data == b'\r\n' or (self._config.allow_bare_lf and data == b'\n'):
            return ParsedHttpTrailers(
                raw_headers=[],
                headers=ParsedHttpHeaders(),
            )

        ctx = _HttpParseContext(
            data=bytes(data),
            config=self._config,
            mode=HttpParser.Mode.AUTO,
        )

        # Verify terminator (trailers end with an empty CRLF line, same as headers)
        ctx.verify_terminator()

        # Parse fields starting at position 0 (no start-line)
        raw_headers = ctx.parse_header_fields(0)

        # Build normalized headers
        headers = ParsedHttpHeaders()
        for rh in raw_headers:
            name_str = rh.name.decode('ascii').lower()
            value_str = rh.value.decode('latin-1')
            headers._add(name_str, value_str)  # noqa

        # Enforce forbidden trailer fields (RFC 7230 §4.1.2)
        for name in headers:
            if name in _HttpParseContext._FORBIDDEN_TRAILER_FIELDS:  # noqa
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.FORBIDDEN_TRAILER_FIELD,
                    message=f'Forbidden field in trailers: {name!r}',
                )

        return ParsedHttpTrailers(
            raw_headers=raw_headers,
            headers=headers,
        )


class _HttpParseContext:
    def __init__(
            self,
            data: Bytes,
            config: HttpParser.Config,
            mode: HttpParser.Mode,
    ) -> None:
        super().__init__()

        self.data = data
        self.config = config
        self.mode = mode
        self.current_line = 0  # 0-indexed logical line number

    # Character constants

    # RFC 7230 §3.2.6: token = 1*tchar
    # tchar = "!" / "#" / "$" / "%" / "&" / "'" / "*" / "+" / "-" / "." / "^" / "_" / "`" / "|" / "~" / DIGIT / ALPHA
    _TCHAR_EXTRAS: ta.ClassVar[ta.FrozenSet[int]] = frozenset(b"!#$%&'*+-.^_`|~")

    _TCHAR: ta.ClassVar[ta.FrozenSet[int]] = frozenset(
        set(range(0x30, 0x3A)) |  # DIGIT 0-9
        set(range(0x41, 0x5B)) |  # ALPHA A-Z
        set(range(0x61, 0x7B)) |  # ALPHA a-z
        _TCHAR_EXTRAS,
    )

    # VCHAR = %x21-7E
    _VCHAR: ta.ClassVar[ta.FrozenSet[int]] = frozenset(range(0x21, 0x7F))

    # obs-text = %x80-FF
    _OBS_TEXT: ta.ClassVar[ta.FrozenSet[int]] = frozenset(range(0x80, 0x100))

    _SP = 0x20
    _HTAB = 0x09
    _CR = 0x0D
    _LF = 0x0A
    _COLON = 0x3A
    _NUL = 0x00

    # OWS = *( SP / HTAB )
    _OWS_CHARS: ta.ClassVar[ta.FrozenSet[int]] = frozenset({_SP, _HTAB})

    _CRLF = b'\r\n'
    _CRLFCRLF = b'\r\n\r\n'

    # Allowed characters as raw bytes for translate()
    _TCHAR_BYTES = bytes(sorted(_TCHAR))
    _VCHAR_BYTES = bytes(range(0x21, 0x7F))

    # Terminator verification

    def verify_terminator(self) -> None:
        data = self.data

        if not self.config.allow_bare_lf:
            # Strict: the first (hence only) empty line must be CRLFCRLF and must sit at the very end - nothing may
            # follow the header terminator.
            idx = data.find(self._CRLFCRLF)
            if idx < 0:
                raise HeaderFieldHttpParseError(
                    code=HeaderFieldHttpParseErrorCode.MISSING_TERMINATOR,
                    message='Header block does not end with CRLFCRLF',
                    line=0,
                    offset=len(data),
                )

            after = idx + 4
            if after < len(data):
                raise HeaderFieldHttpParseError(
                    code=HeaderFieldHttpParseErrorCode.TRAILING_DATA,
                    message=f'Unexpected {len(data) - after} byte(s) after header terminator',
                    line=0,
                    offset=after,
                )

            return

        # Bare-LF allowed: line endings may be LF or CRLF, so the terminating empty line can be LFLF, CRLF-LF, LF-CRLF
        # or CRLFCRLF - i.e. the data must end with LFLF or LF-CRLF. We must NOT reuse the strict 'first CRLFCRLF at
        # end' rule here: an earlier bare-LF empty line is the real terminator, and honoring a later CRLFCRLF instead
        # would silently drop the fields in between. parse_header_fields stops at the FIRST empty line and
        # authoritatively rejects anything after it; here we only require that some terminator exists so a truly
        # unterminated block is reported cleanly and early.
        if data.endswith((b'\n\n', b'\n\r\n')):
            return

        raise HeaderFieldHttpParseError(
            code=HeaderFieldHttpParseErrorCode.MISSING_TERMINATOR,
            message='Header block does not end with an empty line',
            line=0,
            offset=len(data),
        )

    # Line utilities

    def find_line_end(self, start: int) -> int:
        """
        Find the end of the current line (position of CR before CRLF, or LF if bare-LF allowed). Returns the index of
        the first byte of the line-ending sequence.

        Uses bytes.find() for NUL/CR/LF rather than iterating byte-by-byte in Python. Only loops when a bare CR must be
        skipped (allow_bare_cr_in_value mode).
        """

        data = self.data
        length = len(data)
        pos = start

        while True:
            # Let C-level .find() locate the first occurrence of each interesting byte.
            cr_at = data.find(b'\r', pos)
            lf_at = data.find(b'\n', pos)

            # Replace "not found" (-1) with length so min() picks the real hits.
            if cr_at < 0:
                cr_at = length
            if lf_at < 0:
                lf_at = length

            # NUL is always an error; only search for it within the current line (bounded by the nearest CR/LF)
            # instead of scanning to the end of the buffer on every line.
            nul_at = data.find(b'\x00', pos, min(cr_at, lf_at))
            if nul_at < 0:
                nul_at = length

            first = min(nul_at, cr_at, lf_at)

            if first == length:
                # None of the three bytes found before end of data.
                break

            # NUL: always an error
            if first == nul_at and nul_at <= cr_at and nul_at <= lf_at:
                raise HeaderFieldHttpParseError(
                    code=HeaderFieldHttpParseErrorCode.NUL_IN_HEADER,
                    message='NUL byte in header data',
                    line=self.current_line,
                    offset=nul_at,
                )

            # CR: check for CRLF vs bare CR
            if first == cr_at and cr_at <= lf_at:
                if cr_at + 1 < length and data[cr_at + 1] == self._LF:
                    return cr_at  # CRLF - this is the line ending

                # Bare CR (not followed by LF)
                if not self.config.allow_bare_cr_in_value:
                    raise HeaderFieldHttpParseError(
                        code=HeaderFieldHttpParseErrorCode.BARE_CARRIAGE_RETURN,
                        message='Bare CR not followed by LF',
                        line=self.current_line,
                        offset=cr_at,
                    )

                # Bare CR is allowed in values - skip past it and search again.
                pos = cr_at + 1
                continue

            # LF: bare LF (if it were preceded by CR we'd have returned above)
            if self.config.allow_bare_lf:
                return lf_at

            raise HeaderFieldHttpParseError(
                code=HeaderFieldHttpParseErrorCode.BARE_LF,
                message='Bare LF without preceding CR',
                line=self.current_line,
                offset=lf_at,
            )

        raise HeaderFieldHttpParseError(
            code=HeaderFieldHttpParseErrorCode.MISSING_TERMINATOR,
            message='Unexpected end of data while scanning for line ending',
            line=self.current_line,
            offset=length,
        )

    def line_ending_len(self, line_end_pos: int) -> int:
        """Return the length of the line ending at *line_end_pos* (1 for LF, 2 for CRLF)."""

        if line_end_pos < len(self.data) and self.data[line_end_pos] == self._LF:
            return 1  # bare LF
        return 2  # CRLF

    # Kind detection

    def detect_kind(self, start_line: Bytes) -> ParsedHttpMessage.Kind:
        if self.mode == HttpParser.Mode.REQUEST:
            return ParsedHttpMessage.Kind.REQUEST

        if self.mode == HttpParser.Mode.RESPONSE:
            return ParsedHttpMessage.Kind.RESPONSE

        # AUTO: responses start with "HTTP/"
        if start_line.startswith(b'HTTP/'):
            return ParsedHttpMessage.Kind.RESPONSE

        return ParsedHttpMessage.Kind.REQUEST

    # Start-line parsing

    _REQUEST_TARGET_BYTES: ta.ClassVar[bytes] = bytes(set(_VCHAR_BYTES) | set(range(0x80, 0x100)))

    def parse_request_line(self, line: Bytes) -> ParsedHttpMessage.RequestLine:
        """Parse ``method SP request-target SP HTTP-version``."""

        # Must have exactly two SP separators

        first_sp = line.find(b' ')
        if first_sp < 0:
            raise StartLineHttpParseError(
                code=StartLineHttpParseErrorCode.MALFORMED_REQUEST_LINE,
                message='No SP found in request-line',
                line=0,
                offset=0,
            )

        last_sp = line.rfind(b' ')
        if first_sp == last_sp:
            raise StartLineHttpParseError(
                code=StartLineHttpParseErrorCode.MALFORMED_REQUEST_LINE,
                message='Only one SP found in request-line; expected method SP target SP version',
                line=0,
                offset=first_sp,
            )

        method_bytes = line[:first_sp]
        target_bytes = line[first_sp + 1:last_sp]
        version_bytes = line[last_sp + 1:]

        # Validate no extra SP in components: check that second SP search from first_sp+1 matches last_sp - i.e., the
        # target does not contain the last SP. Actually the HTTP spec says request-target can contain spaces? No - it's
        # defined as *visible ASCII*. But to find the correct split: method is a token (no SP), version is fixed format
        # (no SP), and everything in between is the target which is VCHAR (no SP). However, some real URIs... no, VCHAR
        # excludes SP. Let's be strict: Check there are exactly 2 SPs total.
        if line.count(b' ') != 2:
            raise StartLineHttpParseError(
                code=StartLineHttpParseErrorCode.MALFORMED_REQUEST_LINE,
                message=f'Request-line contains {line.count(b" ")} spaces; expected exactly 2',
                line=0,
                offset=0,
            )

        # Validate method

        if not method_bytes:
            raise StartLineHttpParseError(
                code=StartLineHttpParseErrorCode.INVALID_METHOD,
                message='Empty method in request-line',
                line=0,
                offset=0,
            )

        if method_bytes.translate(None, self._TCHAR_BYTES):
            raise StartLineHttpParseError(
                code=StartLineHttpParseErrorCode.INVALID_METHOD,
                message=f'Method contains invalid character(s)',
                line=0,
                offset=0,
            )

        # Validate request-target (VCHAR only, non-empty)

        if not target_bytes:
            raise StartLineHttpParseError(
                code=StartLineHttpParseErrorCode.INVALID_REQUEST_TARGET,
                message='Empty request-target',
                line=0,
                offset=first_sp + 1,
            )

        if self.config.reject_non_visible_ascii_request_target:
            if target_bytes.translate(None, self._VCHAR_BYTES):
                raise StartLineHttpParseError(
                    code=StartLineHttpParseErrorCode.INVALID_REQUEST_TARGET,
                    message='Request-target contains non-visible-ASCII character(s)',
                    line=0,
                    offset=first_sp + 1,
                )

        else:
            if target_bytes.translate(None, self._REQUEST_TARGET_BYTES):
                raise StartLineHttpParseError(
                    code=StartLineHttpParseErrorCode.INVALID_REQUEST_TARGET,
                    message='Request-target contains invalid character(s)',
                    line=0,
                    offset=first_sp + 1,
                )

        # Validate HTTP version

        version_str = version_bytes.decode('ascii', errors='replace')
        if version_str == 'HTTP/1.0':
            version = HttpVersions.HTTP_1_0
        elif version_str == 'HTTP/1.1':
            version = HttpVersions.HTTP_1_1
        else:
            raise StartLineHttpParseError(
                code=StartLineHttpParseErrorCode.UNSUPPORTED_HTTP_VERSION,
                message=f'Unsupported HTTP version: {version_str!r}',
                line=0,
                offset=last_sp + 1,
            )

        return ParsedHttpMessage.RequestLine(
            method=method_bytes.decode('ascii'),
            request_target=target_bytes,
            http_version=version,
        )

    # reason-phrase: 0+ bytes of HTAB / SP / VCHAR / obs-text
    _RE_REASON_PHRASE: ta.ClassVar[re.Pattern] = re.compile(rb'^[\x09\x20\x21-\x7e\x80-\xff]*\Z')

    # reason-phrase = *( HTAB / SP / VCHAR / obs-text )
    _REASON_PHRASE_CHARS: ta.ClassVar[ta.FrozenSet[int]] = frozenset(
        {_HTAB, _SP} |
        set(_VCHAR) |
        set(_OBS_TEXT),
    )

    def parse_status_line(self, line: Bytes) -> ParsedHttpMessage.StatusLine:
        """Parse ``HTTP-version SP status-code SP reason-phrase``."""

        # First SP separates version from status code

        first_sp = line.find(b' ')
        if first_sp < 0:
            raise StartLineHttpParseError(
                code=StartLineHttpParseErrorCode.MALFORMED_STATUS_LINE,
                message='No SP found in status-line',
                line=0,
                offset=0,
            )

        version_bytes = line[:first_sp]
        rest = line[first_sp + 1:]

        # Second SP separates status code from reason phrase

        second_sp = rest.find(b' ')
        if second_sp < 0:
            # Per RFC 7230:
            #   `status-line = HTTP-version SP status-code SP reason-phrase`.
            # The SP before reason-phrase is required even if reason-phrase is empty.
            raise StartLineHttpParseError(
                code=StartLineHttpParseErrorCode.MALFORMED_STATUS_LINE,
                message='Missing second SP in status-line (required before reason-phrase)',
                line=0,
                offset=first_sp + 1 + len(rest),
            )

        status_bytes = rest[:second_sp]
        reason_bytes = rest[second_sp + 1:]

        # Validate HTTP version

        version_str = version_bytes.decode('ascii', errors='replace')
        if version_str == 'HTTP/1.0':
            version = HttpVersions.HTTP_1_0
        elif version_str == 'HTTP/1.1':
            version = HttpVersions.HTTP_1_1
        else:
            raise StartLineHttpParseError(
                code=StartLineHttpParseErrorCode.UNSUPPORTED_HTTP_VERSION,
                message=f'Unsupported HTTP version: {version_str!r}',
                line=0,
                offset=0,
            )

        # Validate status code: exactly 3 ASCII digits

        if len(status_bytes) != 3 or not status_bytes.isdigit():
            raise StartLineHttpParseError(
                code=StartLineHttpParseErrorCode.INVALID_STATUS_CODE,
                message=f'Status code is not exactly 3 digits: {status_bytes!r}',
                line=0,
                offset=first_sp + 1,
            )

        status_code = int(status_bytes)
        if not (100 <= status_code <= 599):
            raise StartLineHttpParseError(
                code=StartLineHttpParseErrorCode.INVALID_STATUS_CODE,
                message=f'Status code {status_code} out of range 100-599',
                line=0,
                offset=first_sp + 1,
            )

        # Validate reason-phrase characters

        if not self._RE_REASON_PHRASE.match(reason_bytes):
            # Regex rejected - scan to find the specific bad byte for error reporting. NUL cannot occur here: it is
            # already rejected by find_line_end before the status line is split off.
            reason_base_offset = first_sp + 1 + second_sp + 1

            for i, b in enumerate(reason_bytes):
                if b not in self._REASON_PHRASE_CHARS:
                    raise StartLineHttpParseError(
                        code=StartLineHttpParseErrorCode.MALFORMED_STATUS_LINE,
                        message=f'Invalid character 0x{b:02x} in reason-phrase',
                        line=0,
                        offset=reason_base_offset + i,
                    )

        # obs-text is permitted in a reason-phrase by RFC 7230, but reject_obs_text asks us to refuse it everywhere.
        if self.config.reject_obs_text:
            reason_base_offset = first_sp + 1 + second_sp + 1

            for i, b in enumerate(reason_bytes):
                if b in self._OBS_TEXT:
                    raise EncodingHttpParseError(
                        code=EncodingHttpParseErrorCode.OBS_TEXT_IN_FIELD_VALUE,
                        message=f'obs-text byte 0x{b:02x} in reason-phrase rejected by config',
                        line=0,
                        offset=reason_base_offset + i,
                    )

        return ParsedHttpMessage.StatusLine(
            http_version=version,
            status_code=status_code,
            reason_phrase=reason_bytes.decode('latin-1'),
        )

    # Header field parsing

    def parse_header_fields(self, start: int) -> ta.List[RawParsedHttpHeader]:
        """Parse all header fields from *start* until the empty-line terminator."""

        headers: ta.List[RawParsedHttpHeader] = []
        pos = start
        data = self.data
        self.current_line = 1  # line 0 is the start-line

        while pos < len(data):
            # Check for the empty line that terminates headers. Whichever empty-line form we stop at, nothing may follow
            # it: this is the authoritative trailing-data check. verify_terminator only gates existence and in bare-LF
            # mode cannot tell which empty line parsing will actually stop at.
            if data[pos] == self._CR and pos + 1 < len(data) and data[pos + 1] == self._LF:
                # \r\n at the start of a "line" = empty line = terminator.
                if pos + 2 != len(data):
                    raise HeaderFieldHttpParseError(
                        code=HeaderFieldHttpParseErrorCode.TRAILING_DATA,
                        message=f'Unexpected {len(data) - (pos + 2)} byte(s) after header terminator',
                        line=self.current_line,
                        offset=pos + 2,
                    )
                break

            if self.config.allow_bare_lf and data[pos] == self._LF:
                if pos + 1 != len(data):
                    raise HeaderFieldHttpParseError(
                        code=HeaderFieldHttpParseErrorCode.TRAILING_DATA,
                        message=f'Unexpected {len(data) - (pos + 1)} byte(s) after header terminator',
                        line=self.current_line,
                        offset=pos + 1,
                    )
                break

            # Max header count check
            if len(headers) >= self.config.max_header_count:
                raise HeaderFieldHttpParseError(
                    code=HeaderFieldHttpParseErrorCode.TOO_MANY_HEADERS,
                    message=f'Exceeded maximum header count of {self.config.max_header_count}',
                    line=self.current_line,
                    offset=pos,
                )

            # Find end of this header line
            line_end = self.find_line_end(pos)
            line_data = data[pos:line_end]
            next_pos = line_end + self.line_ending_len(line_end)

            if self.config.max_header_length is not None and len(line_data) > self.config.max_header_length:
                raise HeaderFieldHttpParseError(
                    code=HeaderFieldHttpParseErrorCode.INVALID_FIELD_VALUE,
                    message='Header line exceeds maximum length',
                    line=self.current_line,
                    offset=pos,
                )

            # Handle obs-fold: if the *next* line starts with SP or HTAB, it's a continuation
            obs_buf: ta.Optional[io.BytesIO] = None

            while next_pos < len(data):
                next_byte = data[next_pos]

                if next_byte in self._OWS_CHARS:
                    if not self.config.allow_obs_fold:
                        raise HeaderFieldHttpParseError(
                            code=HeaderFieldHttpParseErrorCode.OBS_FOLD_NOT_ALLOWED,
                            message='Obsolete line folding (obs-fold) encountered but not allowed',
                            line=self.current_line,
                            offset=next_pos,
                        )

                    # Unfold: find the end of the continuation line
                    cont_line_end = self.find_line_end(next_pos)
                    cont_data = data[next_pos:cont_line_end]

                    # Replace fold with single SP
                    if obs_buf is None:
                        obs_buf = io.BytesIO()
                        obs_buf.write(line_data)
                    obs_buf.write(b' ')
                    obs_buf.write(cont_data.lstrip(b' \t'))

                    next_pos = cont_line_end + self.line_ending_len(cont_line_end)

                    # Continuation lines are physical lines too - keep current_line aligned with the byte offsets so
                    # errors after a folded header point at the right line.
                    self.current_line += 1

                    if self.config.max_header_length is not None and obs_buf.tell() > self.config.max_header_length:
                        raise HeaderFieldHttpParseError(
                            code=HeaderFieldHttpParseErrorCode.INVALID_FIELD_VALUE,
                            message='Unfolded header line exceeds maximum length',
                            line=self.current_line,
                            offset=next_pos,
                        )

                else:
                    break

            if obs_buf is not None:
                line_data = obs_buf.getvalue()

            # Parse field-name : field-value
            header = self._parse_one_header(line_data, pos)
            headers.append(header)

            pos = next_pos
            self.current_line += 1

        return headers

    @classmethod
    def _strip_ows_bytes(cls, data: Bytes) -> Bytes:
        """Strip leading and trailing optional whitespace (SP / HTAB)."""

        return data.strip(b' \t')

    @classmethod
    def _strip_ows_str(cls, s: str) -> str:
        """
        Strip only HTTP OWS (SP / HTAB) from a str.

        ``str.strip()`` with no argument also removes Unicode whitespace such as U+0085 and U+00A0. Those are reachable
        here: obs-text bytes (0x80-0xFF) are permitted in field values by default and decode (latin-1) to exactly those
        codepoints, so bare ``strip()`` would silently discard bytes a peer keeps - a parser-differential / smuggling
        risk. HTTP OWS is only SP and HTAB, so strip exactly those.
        """

        return s.strip(' \t')

    # token: 1+ tchar bytes
    _RE_TOKEN: ta.ClassVar[re.Pattern] = re.compile(rb"^[!#$%&'*+\-.^_`|~0-9A-Za-z]+\Z")

    @classmethod
    def _is_token(cls, s: str) -> bool:
        # Tokens are ASCII-only by definition (tchar), so encoding the latin-1-decoded value back to latin-1 is lossless
        # here. (Same trick as the header field-name check.)
        return cls._RE_TOKEN.match(s.encode('latin-1')) is not None

    # Pre-calculate the 4 field-value variants for the translation filter (allow_bare_cr, reject_obs_text)
    _FIELD_VALUE_ALLOWED: ta.ClassVar[ta.Mapping[ta.Tuple[bool, bool], bytes]] = {
        (False, False): bytes({_HTAB, _SP}      | set(range(0x21, 0x7F))   | set(range(0x80, 0x100))),  # noqa
        (False, True):  bytes({_HTAB, _SP}      | set(range(0x21, 0x7F))),  # noqa
        (True, False):  bytes({_HTAB, _CR, _SP} | set(range(0x21, 0x7F))   | set(range(0x80, 0x100))),  # noqa
        (True, True):   bytes({_HTAB, _CR, _SP} | set(range(0x21, 0x7F))),  # noqa
    }

    def _parse_one_header(self, line_data: Bytes, line_start_offset: int) -> RawParsedHttpHeader:
        """Parse a single ``field-name: field-value`` line (already unfolded)."""

        colon_idx = line_data.find(b':')
        if colon_idx < 0:
            raise HeaderFieldHttpParseError(
                code=HeaderFieldHttpParseErrorCode.MISSING_COLON,
                message='Header line has no colon separator',
                line=self.current_line,
                offset=line_start_offset,
            )

        name_bytes = line_data[:colon_idx]
        value_bytes = line_data[colon_idx + 1:]

        # Validate field-name

        if not name_bytes:
            raise HeaderFieldHttpParseError(
                code=HeaderFieldHttpParseErrorCode.EMPTY_FIELD_NAME,
                message='Empty field-name before colon',
                line=self.current_line,
                offset=line_start_offset,
            )

        # Check for space before colon
        if name_bytes[-1] in self._OWS_CHARS:
            if not self.config.dangerous_allow_space_before_colon:
                raise HeaderFieldHttpParseError(
                    code=HeaderFieldHttpParseErrorCode.SPACE_BEFORE_COLON,
                    message='Whitespace between field-name and colon',
                    line=self.current_line,
                    offset=line_start_offset + len(name_bytes) - 1,
                )

            # Strip trailing whitespace from name if allowed
            name_bytes = name_bytes.rstrip(b' \t')
            if not name_bytes:
                raise HeaderFieldHttpParseError(
                    code=HeaderFieldHttpParseErrorCode.EMPTY_FIELD_NAME,
                    message='Field-name is only whitespace before colon',
                    line=self.current_line,
                    offset=line_start_offset,
                )

        # Validate name characters (regex fast-path; fallback scan on failure)
        if not self._RE_TOKEN.match(name_bytes):
            for i, b in enumerate(name_bytes):
                if b == self._NUL:
                    raise HeaderFieldHttpParseError(
                        code=HeaderFieldHttpParseErrorCode.NUL_IN_HEADER,
                        message='NUL byte in field-name',
                        line=self.current_line,
                        offset=line_start_offset + i,
                    )

                if b >= 0x80:
                    raise EncodingHttpParseError(
                        code=EncodingHttpParseErrorCode.NON_ASCII_IN_FIELD_NAME,
                        message=f'Non-ASCII byte 0x{b:02x} in field-name',
                        line=self.current_line,
                        offset=line_start_offset + i,
                    )

                if b not in self._TCHAR:
                    raise HeaderFieldHttpParseError(
                        code=HeaderFieldHttpParseErrorCode.INVALID_FIELD_NAME,
                        message=f'Invalid character 0x{b:02x} in field-name',
                        line=self.current_line,
                        offset=line_start_offset + i,
                    )

        # Process field-value

        # Strip OWS
        value_stripped = self._strip_ows_bytes(value_bytes)

        # Check for empty value
        if not value_stripped and self.config.reject_empty_header_values:
            raise HeaderFieldHttpParseError(
                code=HeaderFieldHttpParseErrorCode.INVALID_FIELD_VALUE,
                message='Empty header field value not allowed',
                line=self.current_line,
                offset=line_start_offset + colon_idx + 1,
            )

        # Validate value characters (Translation fast-path)
        allowed_bytes = self._FIELD_VALUE_ALLOWED[(
            self.config.allow_bare_cr_in_value,
            self.config.reject_obs_text,
        )]

        # This is the "Pedantic" C-speed check. translate(None, allowed_bytes) removes all valid characters. If any
        # bytes remain, the input is invalid.
        invalid_chars = value_stripped.translate(None, allowed_bytes)

        if invalid_chars:
            value_base_offset = line_start_offset + colon_idx + 1
            # We only enter this Python loop if we ALREADY found an error. This keeps the "happy path" fast while
            # maintaining detailed error reporting.
            for i, b in enumerate(value_stripped):
                if b == self._NUL:
                    raise HeaderFieldHttpParseError(
                        code=HeaderFieldHttpParseErrorCode.NUL_IN_HEADER,
                        message='NUL byte in field-value',
                        line=self.current_line,
                        offset=value_base_offset + i,
                    )

                if b == self._CR:
                    if not self.config.allow_bare_cr_in_value:
                        raise HeaderFieldHttpParseError(
                            code=HeaderFieldHttpParseErrorCode.BARE_CARRIAGE_RETURN,
                            message='Bare CR in field-value',
                            line=self.current_line,
                            offset=value_base_offset + i,
                        )
                    continue

                if b not in allowed_bytes:
                    # Specific error logic for obs-text/bare CR
                    if b >= 0x80 and self.config.reject_obs_text:
                        raise EncodingHttpParseError(
                            code=EncodingHttpParseErrorCode.OBS_TEXT_IN_FIELD_VALUE,
                            message=f'obs-text byte 0x{b:02x} rejected by config',
                            line=self.current_line,
                            offset=value_base_offset + i,
                        )

                    # General character error
                    raise HeaderFieldHttpParseError(
                        code=HeaderFieldHttpParseErrorCode.INVALID_FIELD_VALUE,
                        message=f'Invalid character 0x{b:02x} in field-value',
                        line=self.current_line,
                        offset=value_base_offset + i,
                    )

        return RawParsedHttpHeader(
            name=name_bytes,
            value=value_stripped,
        )

    # Prepared header construction

    def prepare_headers(
        self,
        headers: ParsedHttpHeaders,
        kind: ParsedHttpMessage.Kind,
        http_version: HttpVersion,
    ) -> PreparedParsedHttpHeaders:
        prepared = PreparedParsedHttpHeaders()

        self._prepare_content_length(headers, prepared)
        self._prepare_transfer_encoding(headers, prepared, kind, http_version)
        self._prepare_host(headers, prepared, kind, http_version)
        self._prepare_connection(headers, prepared, http_version)
        self._prepare_content_type(headers, prepared)
        self._prepare_te(headers, prepared, kind, http_version)
        self._prepare_upgrade(headers, prepared, http_version)
        self._prepare_trailer(headers, prepared)
        self._prepare_expect(headers, prepared, kind)
        self._prepare_date(headers, prepared)
        self._prepare_cache_control(headers, prepared)
        self._prepare_accept_encoding(headers, prepared)
        self._prepare_accept(headers, prepared)
        self._prepare_authorization(headers, prepared)

        # Cross-field: Content-Length + Transfer-Encoding conflict
        if (
            prepared.content_length is not None and
            prepared.transfer_encoding is not None and
            not self.config.allow_content_length_with_te
        ):
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.CONTENT_LENGTH_WITH_TRANSFER_ENCODING,
                message='Content-Length and Transfer-Encoding are both present',
            )

        # Cross-field: an Upgrade header is only meaningful when the 'upgrade' connection option is also present
        # (RFC 7230 §6.7). _prepare_connection always sets connection (to an empty frozenset when the header is
        # absent), but narrow for the type checker anyway.
        if (
            prepared.upgrade is not None and
            prepared.connection is not None and
            'upgrade' not in prepared.connection and
            not self.config.allow_upgrade_without_connection_upgrade
        ):
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.UPGRADE_WITHOUT_CONNECTION_UPGRADE,
                message='Upgrade header present without a corresponding "upgrade" Connection option',
            )

        return prepared

    def _prepare_content_length(self, headers: ParsedHttpHeaders, prepared: PreparedParsedHttpHeaders) -> None:
        values = headers.get_all('content-length')
        if not values:
            return

        parsed_values: ta.List[int] = []
        for v in values:
            # A single Content-Length header might itself be a comma-separated list (some implementations do this). We
            # parse each element.
            if self.config.reject_multi_value_content_length and ',' in v:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_CONTENT_LENGTH,
                    message=f'Content-Length with multiple values is forbidden: {v!r}',
                )

            for part in v.split(','):
                stripped = self._strip_ows_str(part)

                # NOTE: must be ASCII digits only. str.isdigit() is True for non-ASCII numerics present in the
                # latin-1-decoded value (e.g. superscripts U+00B2/B3/B9); int() rejects those with a ValueError. Also,
                # obs-text bytes that decode to Unicode whitespace (U+0085, U+00A0) are permitted in a field value by
                # default - stripping only ASCII OWS above keeps them here so isascii() rejects them rather than
                # silently treating '42\xa0' as '42'.
                if not (stripped.isascii() and stripped.isdigit()):
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_CONTENT_LENGTH,
                        message=f'Content-Length value is not a valid non-negative integer: {stripped!r}',
                    )

                if (
                        self.config.max_content_length_str_len is not None and
                        len(stripped) > self.config.max_content_length_str_len
                ):
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_CONTENT_LENGTH,
                        message=f'Content-Length value string too long: {stripped!r}',
                    )

                # int() raises ValueError above sys.get_int_max_str_digits() (default 4300, backported to all maintained
                # 3.8+ releases). max_content_length_str_len bounds this by default, but it may be None, so guard the
                # conversion and surface a clean parse error rather than letting the ValueError escape.
                try:
                    parsed_values.append(int(stripped))
                except ValueError:
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_CONTENT_LENGTH,
                        message=f'Content-Length value could not be parsed as an integer: {stripped!r}',
                    ) from None

        if not parsed_values:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_CONTENT_LENGTH,
                message='Content-Length header present but empty',
            )

        unique = set(parsed_values)
        if len(unique) > 1:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.CONFLICTING_CONTENT_LENGTH,
                message=f'Conflicting Content-Length values: {sorted(unique)}',
            )

        if len(parsed_values) > 1:
            if not self.config.allow_multiple_content_lengths:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.DUPLICATE_CONTENT_LENGTH,
                    message=(
                        f'Multiple Content-Length values (all {parsed_values[0]}); '
                        f'set allow_multiple_content_lengths to accept'
                    ),
                )

        # A negative value is impossible here: isdigit() rejects a leading '-', so parsed_values are all >= 0.
        prepared.content_length = parsed_values[0]

    _KNOWN_CODINGS: ta.ClassVar[ta.FrozenSet[str]] = frozenset([
        'chunked',
        'compress',
        'deflate',
        'gzip',
        'x-gzip',
        'x-compress',
    ])

    def _prepare_transfer_encoding(
        self,
        headers: ParsedHttpHeaders,
        prepared: PreparedParsedHttpHeaders,
        kind: ParsedHttpMessage.Kind,
        http_version: HttpVersion,
    ) -> None:
        if 'transfer-encoding' not in headers:
            return

        combined = headers['transfer-encoding']

        # Quote-aware split; truly-empty elements are ignorable per RFC 9110 §5.6.1, but an all-empty list is not a
        # valid Transfer-Encoding (1#transfer-coding requires at least one coding).
        codings = [s.lower() for s in self._parse_comma_list(combined)]

        if not codings:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_TRANSFER_ENCODING,
                message='Transfer-Encoding header present but empty',
            )

        # transfer-coding is a token (RFC 7230 §4) - checked unconditionally so codings are structurally valid even
        # when unknown codings are allowed.
        for c in codings:
            if not self._is_token(c):
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_TRANSFER_ENCODING,
                    message=f'Transfer-coding is not a valid token: {c!r}',
                )

        # HTTP/1.0 check
        if http_version == HttpVersions.HTTP_1_0 and not self.config.allow_transfer_encoding_http10:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.TRANSFER_ENCODING_IN_HTTP10,
                message='Transfer-Encoding is not defined for HTTP/1.0',
            )

        # Validate known codings
        if not self.config.allow_unknown_transfer_encoding:
            for c in codings:
                if c not in self._KNOWN_CODINGS:
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_TRANSFER_ENCODING,
                        message=f'Unknown transfer-coding: {c!r}',
                    )

        # chunked positioning
        if 'chunked' in codings:
            if codings[-1] != 'chunked':
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.TE_WITHOUT_CHUNKED_LAST,
                    message='chunked must be the last (outermost) transfer-coding',
                )

            if codings.count('chunked') > 1:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_TRANSFER_ENCODING,
                    message='chunked appears more than once in Transfer-Encoding',
                )

        else:
            # No chunked present
            if kind == ParsedHttpMessage.Kind.REQUEST:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.TE_WITHOUT_CHUNKED_LAST,
                    message='Transfer-Encoding in a request must include chunked as the last coding',
                )

            elif kind == ParsedHttpMessage.Kind.RESPONSE:
                if not self.config.allow_te_without_chunked_in_response:
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.TE_WITHOUT_CHUNKED_LAST,
                        message=(
                            'Transfer-Encoding in a response without chunked; '
                            'set allow_te_without_chunked_in_response to accept'
                        ),
                    )

        prepared.transfer_encoding = codings

    # Host header: reject control chars 0x00-0x1F and SP 0x20. # Operates on str (already latin-1 decoded).
    _RE_HOST_VALID: ta.ClassVar[re.Pattern] = re.compile(r'^[^\x00-\x20]*\Z')

    def _prepare_host(
        self,
        headers: ParsedHttpHeaders,
        prepared: PreparedParsedHttpHeaders,
        kind: ParsedHttpMessage.Kind,
        http_version: HttpVersion,
    ) -> None:
        values = headers.get_all('host')

        # The Host header is only defined for requests - a server must not send it, and a client should not accept it
        # (RFC 7230 §5.4, §3.1.2). Previously a Host header in a response was silently stored into prepared.host.
        if kind == ParsedHttpMessage.Kind.RESPONSE and values:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.HOST_IN_RESPONSE,
                message='Host header is only defined for requests',
            )

        if kind == ParsedHttpMessage.Kind.REQUEST and http_version == HttpVersions.HTTP_1_1:
            if not values and not self.config.allow_missing_host:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.MISSING_HOST_HEADER,
                    message='Host header is required in HTTP/1.1 requests',
                )

        if len(values) > 1:
            if not self.config.allow_multiple_hosts:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.MULTIPLE_HOST_HEADERS,
                    message=f'Multiple Host headers found ({len(values)})',
                )

            # If allowed, all values must be identical
            unique = set(values)
            if len(unique) > 1:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.CONFLICTING_HOST_HEADERS,
                    message=f'Multiple Host headers with different values: {sorted(unique)}',
                )

        if values:
            host_val = self._strip_ows_str(values[0])

            # Minimal validation: reject any whitespace/control chars. Host is an authority, and
            # allowing OWS creates parsing inconsistencies across components.
            if not host_val and kind == ParsedHttpMessage.Kind.REQUEST:
                # Empty Host is technically allowed for certain request-targets (authority form, etc.), but let's just
                # accept it - the URI layer handles that.
                pass

            # Reject any SP / HTAB anywhere.
            if ' ' in host_val or '\t' in host_val:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_HOST,
                    message='Whitespace not allowed in Host header',
                )

            # Reject other C0 controls (including NUL) if present (defense in depth). (Host is a str decoded as Latin-1
            # in your ParsedHttpHeaders container.)
            if not self._RE_HOST_VALID.match(host_val):
                for i, ch in enumerate(host_val):
                    if ord(ch) < 0x21:  # includes 0x00-0x20; we've already rejected SP/HTAB explicitly
                        raise SemanticHeaderHttpParseError(
                            code=SemanticHeaderHttpParseErrorCode.INVALID_HOST,
                            message=f'Invalid character in Host header at position {i}',
                        )

            prepared.host = host_val

    @classmethod
    def _parse_comma_list(cls, value: str) -> ta.List[str]:
        """
        Split a comma-separated header value into trimmed, non-empty tokens.

        Quoted-string aware: a comma inside a quoted-string does not separate list elements (RFC 9110 §5.6.1). A strict
        parser must not split on it - blindly splitting mangles valid values like ``Accept: text/html;level="1,2"`` into
        a truncated token and turns the remainder into bogus extra elements.
        """

        parts: ta.List[str] = []
        buf: ta.List[str] = []
        in_quotes = False

        i = 0
        n = len(value)
        while i < n:
            ch = value[i]

            if in_quotes:
                if ch == '\\' and i + 1 < n:
                    buf.append(value[i:i + 2])
                    i += 2
                    continue

                if ch == '"':
                    in_quotes = False

                buf.append(ch)
                i += 1
                continue

            if ch == '"':
                in_quotes = True
                buf.append(ch)
                i += 1
                continue

            if ch == ',':
                stripped = cls._strip_ows_str(''.join(buf))
                if stripped:
                    parts.append(stripped)
                buf = []
                i += 1
                continue

            buf.append(ch)
            i += 1

        stripped = cls._strip_ows_str(''.join(buf))
        if stripped:
            parts.append(stripped)

        return parts

    def _prepare_connection(
        self,
        headers: ParsedHttpHeaders,
        prepared: PreparedParsedHttpHeaders,
        http_version: HttpVersion,
    ) -> None:
        if 'connection' in headers:
            # Truly-empty elements are ignorable per RFC 9110 §5.6.1.
            tokens = {t.lower() for t in self._parse_comma_list(headers['connection'])}

            # Connection = 1#connection-option (RFC 7230 §6.1): the header being present requires at least one option -
            # otherwise it is indistinguishable from (and silently conflated with) an absent header.
            if not tokens:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_CONNECTION,
                    message='Connection header present but empty',
                )

            # connection-option is a token (RFC 7230 §6.1).
            for t in tokens:
                if not self._is_token(t):
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_CONNECTION,
                        message=f'Connection option is not a valid token: {t!r}',
                    )

            prepared.connection = frozenset(tokens)
        else:
            prepared.connection = frozenset()

        # Derive keep_alive
        if 'close' in prepared.connection:
            prepared.keep_alive = False
        elif 'keep-alive' in prepared.connection:
            prepared.keep_alive = True
        else:
            # Default: HTTP/1.1 = keep-alive, HTTP/1.0 = close
            prepared.keep_alive = (http_version == HttpVersions.HTTP_1_1)

    @classmethod
    def _parse_quoted_string(cls, data: str, pos: int) -> ta.Tuple[str, int]:
        """
        Parse a quoted-string starting at *pos* (which must point at the opening DQUOTE). Returns (unescaped_value,
        position_after_closing_DQUOTE).
        """

        if pos >= len(data) or data[pos] != '"':
            raise ValueError('Expected opening double-quote')

        pos += 1  # skip opening "

        result: ta.List[str] = []
        while pos < len(data):
            ch = data[pos]

            if ch == '"':
                return ''.join(result), pos + 1

            if ch == '\\':
                pos += 1
                if pos >= len(data):
                    raise ValueError('Backslash at end of quoted-string')
                result.append(data[pos])
                pos += 1

            else:
                result.append(ch)
                pos += 1

        raise ValueError('Unterminated quoted-string')

    @classmethod
    def _parse_media_type_params(
        cls,
        params_str: str,
        quoted_params: ta.Optional[ta.Set[str]] = None,
    ) -> ta.Dict[str, str]:
        """
        Parse ``;param=value`` segments from a Content-Type or Accept header. Values may be tokens or quoted-strings.

        Pedantic: parameter names must be tokens, bare (unquoted) values must be tokens, nothing may follow a
        quoted-string value except OWS and the next parameter, duplicates are rejected, and a parameter with no ``=`` is
        an error rather than being silently skipped (RFC 9110 §5.6.6). When *quoted_params* is given it is filled with
        the names of parameters whose values were quoted-strings: qvalues must be bare tokens, so this lets qvalue-aware
        callers reject quoted forms like ``q="0.5"``.
        """

        params: ta.Dict[str, str] = {}

        remaining = cls._strip_ows_str(params_str)
        while remaining:
            if not remaining.startswith(';'):
                raise ValueError(f'Unexpected content in parameters: {remaining!r}')

            remaining = cls._strip_ows_str(remaining[1:])
            if not remaining:
                break  # a trailing ';' is tolerated (common in the wild)

            eq_idx = remaining.find('=')
            if eq_idx < 0:
                # parameter name without value - garbage, not a legal parameter (RFC 9110 §5.6.6)
                raise ValueError(f'Parameter without a value: {remaining!r}')

            pname = cls._strip_ows_str(remaining[:eq_idx]).lower()

            # parameter-name is a token (RFC 9110 §5.6.6)
            if not pname or not cls._is_token(pname):
                raise ValueError(f'Parameter name is not a valid token: {pname!r}')

            remaining = cls._strip_ows_str(remaining[eq_idx + 1:])

            if remaining.startswith('"'):
                # An unterminated quoted-string would otherwise silently swallow all remaining parameters - surface
                # it instead of pretending the value simply had no parameters.
                pvalue, end_pos = cls._parse_quoted_string(remaining, 0)
                remaining = cls._strip_ows_str(remaining[end_pos:])

                if remaining and not remaining.startswith(';'):
                    # Junk after the closing DQUOTE was previously silently dropped.
                    raise ValueError(f'Unexpected content after quoted parameter value: {remaining!r}')

                if quoted_params is not None:
                    quoted_params.add(pname)

            else:
                semi_idx = remaining.find(';')

                if semi_idx < 0:
                    pvalue = cls._strip_ows_str(remaining)
                    remaining = ''
                else:
                    pvalue = cls._strip_ows_str(remaining[:semi_idx])
                    remaining = remaining[semi_idx:]

                # bare parameter values are tokens (RFC 9110 §5.6.6)
                if not pvalue or not cls._is_token(pvalue):
                    raise ValueError(f'Parameter value is not a valid token: {pvalue!r}')

            if pname in params:
                raise ValueError(f'Duplicate parameter: {pname!r}')

            params[pname] = pvalue

        return params

    def _prepare_content_type(self, headers: ParsedHttpHeaders, prepared: PreparedParsedHttpHeaders) -> None:
        # Content-Type is a singleton header. get_all (not the comma-joining __getitem__): joining two Content-Type
        # values with ', ' would produce a string that still passes the media-type shape checks below, and the parameter
        # parser would then silently keep the second value's parameters - a parser differential.
        values = headers.get_all('content-type')
        if not values:
            return

        if len(values) > 1:
            if not self.config.allow_multiple_content_types:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.MULTIPLE_CONTENT_TYPES,
                    message=f'Multiple Content-Type headers found ({len(values)})',
                )

            # If allowed, all values must agree (mirrors Host handling).
            unique = {v.lower() for v in values}
            if len(unique) > 1:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.CONFLICTING_CONTENT_TYPES,
                    message=f'Multiple Content-Type headers with different values: {sorted(unique)}',
                )

        raw = values[0]

        # media-type = type "/" subtype *( OWS ";" OWS parameter )
        semi_idx = raw.find(';')
        if semi_idx < 0:
            media_type = self._strip_ows_str(raw).lower()
            params: ta.Dict[str, str] = {}
        else:
            media_type = self._strip_ows_str(raw[:semi_idx]).lower()
            try:
                params = self._parse_media_type_params(raw[semi_idx:])
            except ValueError as e:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_CONTENT_TYPE,
                    message=f'Invalid Content-Type parameters: {e}',
                ) from None

        if '/' not in media_type:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_CONTENT_TYPE,
                message=f'Content-Type missing "/" in media-type: {media_type!r}',
            )

        parts = media_type.split('/', 1)
        if not parts[0] or not parts[1]:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_CONTENT_TYPE,
                message=f'Content-Type has empty type or subtype: {media_type!r}',
            )

        # media-type = type "/" subtype, and both type and subtype are tokens (RFC 7231 §3.1.1.1).
        if not self._is_token(parts[0]) or not self._is_token(parts[1]):
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_CONTENT_TYPE,
                message=f'Content-Type type or subtype is not a valid token: {media_type!r}',
            )

        prepared.content_type = PreparedParsedHttpHeaders.ContentType(
            media_type=media_type,
            params=params,
        )

    # RFC 9110 §12.4.2: qvalue = ( "0" [ "." 0*3DIGIT ] ) / ( "1" [ "." 0*3("0") ] ). The lexical form is checked
    # before float(): float() would otherwise accept 'nan', 'inf', exponents, '.5', '01', more than 3 decimals, etc.
    # Note that when a '.' is present at least one digit must follow it ('0.' is invalid).
    _RE_QVALUE: ta.ClassVar[re.Pattern] = re.compile(r'^(?:0(?:\.[0-9]{1,3})?|1(?:\.0{1,3})?)\Z')

    @classmethod
    def _split_header_element(cls, element: str) -> ta.Tuple[str, float, ta.Dict[str, str]]:
        """
        Split a single header list element like ``"token;q=0.5;param=val"`` into ``(token_lower, q, params_dict)``.

        *token* is lowercased.  ``q`` defaults to ``1.0`` if absent.  The ``q`` key is consumed and **not** included in
        *params_dict*.  Raises ``ValueError`` on a malformed ``q`` value or malformed parameters (e.g. an unterminated
        quoted-string); callers wrap it in the appropriate header-specific parse error.

        Pedantic: if present, ``q`` must be the *last* parameter (RFC 9110 §12.4.2: parameters after q are not
        accepted), and it can only appear once - previously ``;q=1;q=0.5`` was silently last-wins, flipping the
        element's semantics.
        """

        semi_idx = element.find(';')
        if semi_idx < 0:
            return cls._strip_ows_str(element).lower(), 1.0, {}

        token = cls._strip_ows_str(element[:semi_idx]).lower()

        quoted_params: ta.Set[str] = set()
        params = cls._parse_media_type_params(element[semi_idx:], quoted_params)

        q_str = None
        # If present, q must be the last parameter - parameters after it are not accepted (RFC 9110 §12.4.2). params
        # preserves insertion order, so check the position of the q key rather than emptiness after popping: q last
        # (e.g. ';level=1;q=0.7') is valid, q anywhere else (e.g. ';q=0.5;level=1') is not. The duplicate-q case is
        # already rejected by _parse_media_type_params as a duplicate parameter.
        if params and list(params)[-1] == 'q':
            q_str = params.pop('q')

        q = 1.0
        if q_str is not None:
            # A qvalue is never a quoted-string (RFC 9110 §12.4.2).
            if 'q' in quoted_params or not cls._RE_QVALUE.match(q_str):
                raise ValueError(f'Invalid qvalue: {q_str!r}')

            q = float(q_str)

        elif 'q' in params:
            raise ValueError('q must be the last parameter')

        return token, q, params

    def _prepare_te(
        self,
        headers: ParsedHttpHeaders,
        prepared: PreparedParsedHttpHeaders,
        kind: ParsedHttpMessage.Kind,
        http_version: HttpVersion,
    ) -> None:
        if 'te' not in headers:
            return

        # The TE header field is only defined within HTTP/1.1 - it must not be sent to an HTTP/1.0 peer (RFC 7230
        # §4.3). (This is the TE header; TRANSFER_ENCODING_IN_HTTP10 covers the Transfer-Encoding header.)
        if http_version == HttpVersions.HTTP_1_0 and not self.config.allow_te_header_http10:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.TE_HEADER_IN_HTTP10,
                message='TE header is not defined for HTTP/1.0',
            )

        # TE is a request-only header field - a server must not send it, and a client should not accept it (RFC 7230
        # §4.3, §5.4). Previously a TE header in a response was parsed and stored without complaint.
        if kind == ParsedHttpMessage.Kind.RESPONSE:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.TE_IN_RESPONSE,
                message='TE header is only defined for requests',
            )

        try:
            elements = [
                self._split_header_element(p)
                for p in self._parse_comma_list(headers['te'])
            ]
        except ValueError:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_TE,
                message=f'Invalid element in TE header: {headers["te"]!r}',
            ) from None

        codings: ta.List[str] = []
        for coding, q, params in elements:
            # A truly empty element is ignorable per RFC 9110 §5.6.1, but an empty token carrying parameters is
            # malformed and must not be silently dropped - previously ';q=0.5' vanished without a trace.
            if not coding:
                if params or q != 1.0:
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_TE,
                        message=f'TE element has an empty coding with parameters: {coding!r}',
                    )
                continue

            # A TE transfer-coding is a token (RFC 7230 §4.3).
            if not self._is_token(coding):
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_TE,
                    message=f'TE transfer-coding is not a valid token: {coding!r}',
                )

            # chunked is not a legal TE coding - it is a Transfer-Encoding coding only, and accepting it here would let
            # a response with 'TE: chunked' be mistaken for a chunked response (RFC 7230 §4.3).
            if coding == 'chunked':
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_TE,
                    message='chunked is not a valid TE coding',
                )

            # A sender of TE MUST NOT accept 'trailers' with a qvalue of 0 (RFC 7230 §4.3).
            if coding == 'trailers' and q == 0.0:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.TE_TRAILERS_Q_ZERO,
                    message='TE header grants "trailers" with a zero qvalue',
                )

            codings.append(coding)

        # The header was present but contains no codings - 1#transfer-coding requires at least one.
        if not codings:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_TE,
                message='TE header present but empty',
            )

        prepared.te = codings

    def _prepare_upgrade(
            self,
            headers: ParsedHttpHeaders,
            prepared: PreparedParsedHttpHeaders,
            http_version: HttpVersion,
    ) -> None:
        if 'upgrade' not in headers:
            return

        # Upgrade is only defined for HTTP/1.1 - it must be ignored (here: rejected) in an HTTP/1.0 request (RFC 7230
        # §6.7).
        if http_version == HttpVersions.HTTP_1_0:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.UPGRADE_IN_HTTP10,
                message='Upgrade header is not defined for HTTP/1.0',
            )

        # Truly-empty elements are ignorable per RFC 9110 §5.6.1.
        protocols = self._parse_comma_list(headers['upgrade'])

        # Upgrade = 1#protocol (RFC 7230 §6.7): present requires at least one protocol.
        if not protocols:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_UPGRADE,
                message='Upgrade header present but empty',
            )

        for p in protocols:
            if '/' in p:
                name, _, version = p.partition('/')
                if not name or not version or not self._is_token(name) or not self._is_token(version):
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_UPGRADE,
                        message=f'Upgrade protocol/version is not a valid token pair: {p!r}',
                    )

            elif not self._is_token(p):
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_UPGRADE,
                    message=f'Upgrade protocol is not a valid token: {p!r}',
                )

        prepared.upgrade = protocols

    # Headers that MUST NOT appear in trailers (RFC 7230 §4.1.2)
    _FORBIDDEN_TRAILER_FIELDS: ta.ClassVar[ta.FrozenSet[str]] = frozenset({
        'transfer-encoding',
        'content-length',
        'host',
        'cache-control',
        'expect',
        'max-forwards',
        'pragma',
        'range',
        'te',
        'authorization',
        'proxy-authenticate',
        'proxy-authorization',
        'www-authenticate',
        'content-encoding',
        'content-type',
        'content-range',
        'trailer',
    })

    def _prepare_trailer(self, headers: ParsedHttpHeaders, prepared: PreparedParsedHttpHeaders) -> None:
        if 'trailer' not in headers:
            return

        # Truly-empty elements are ignorable per RFC 9110 §5.6.1.
        fields = {f.lower() for f in self._parse_comma_list(headers['trailer'])}

        for f in fields:
            # The Trailer header value is a list of field-names, which are tokens (RFC 7230 §4.1.2).
            if not self._is_token(f):
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_TRAILER_FIELD,
                    message=f'Trailer field-name is not a valid token: {f!r}',
                )

            if f in self._FORBIDDEN_TRAILER_FIELDS:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.FORBIDDEN_TRAILER_FIELD,
                    message=f'Forbidden field in Trailer header: {f!r}',
                )

        # Trailer = 1#field-name (RFC 7230 §4.1.2): present requires at least one field-name.
        if not fields:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_TRAILER_FIELD,
                message='Trailer header present but empty',
            )

        prepared.trailer = frozenset(fields)

    def _prepare_expect(
            self,
            headers: ParsedHttpHeaders,
            prepared: PreparedParsedHttpHeaders,
            kind: ParsedHttpMessage.Kind,
    ) -> None:
        if 'expect' not in headers:
            return

        # Expect is a request-only header field (RFC 7231 §5.1.1) - a client must not accept it in a response.
        if kind == ParsedHttpMessage.Kind.RESPONSE:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.EXPECT_IN_RESPONSE,
                message='Expect header is only defined for requests',
            )

        raw = self._strip_ows_str(headers['expect']).lower()
        if raw != '100-continue':
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_EXPECT,
                message=f'Only "100-continue" is accepted for Expect; got {raw!r}',
            )

        prepared.expect = raw
        prepared.expect_100_continue = True

    # datetime.weekday(): Monday is 0, Sunday is 6
    _WEEKDAY_NAMES: ta.ClassVar[ta.Sequence[str]] = ('mon', 'tue', 'wed', 'thu', 'fri', 'sat', 'sun')

    _MONTH_NAMES: ta.ClassVar[ta.Mapping[str, int]] = {
        'jan': 1,
        'feb': 2,
        'mar': 3,
        'apr': 4,
        'may': 5,
        'jun': 6,
        'jul': 7,
        'aug': 8,
        'sep': 9,
        'oct': 10,
        'nov': 11,
        'dec': 12,
    }

    @classmethod
    def _check_http_date_weekday(cls, dt: datetime.datetime, weekday_str: str) -> None:
        """
        Cross-check the given weekday abbreviation against the parsed date. Pedantic: the RFCs define the day-name as
        part of every date format, and accepting a mismatched one silently would mask a mangled (or malicious) value.
        """

        expected = cls._WEEKDAY_NAMES[dt.weekday()]
        if weekday_str.lower() != expected:
            raise ValueError(f'Weekday {weekday_str!r} does not match date (expected {expected!r})')

    @classmethod
    def _date_int(cls, s: str, what: str, min_len: int, max_len: int) -> int:
        """
        Strict integer field for HTTP-date components.

        ``int()`` alone is far too lenient: it accepts leading ``+`` and ``_`` separators (``int('+4') == 4``,
        ``int('1_94') == 194``), arbitrary widths ('8', '008', '0_8'), and surrounding whitespace - all of which would
        silently produce a different date than the one sent. This enforces pure ASCII digits of an exact width range,
        like the Content-Length digit check.
        """

        if (
                not s.isascii() or
                not s.isdigit() or
                not (min_len <= len(s) <= max_len)
        ):
            raise ValueError(f'Invalid {what} component: {s!r}')

        return int(s)

    @classmethod
    def _parse_http_date(cls, value: str) -> datetime.datetime:
        """
        Parse an HTTP-date (RFC 7231 §7.1.1.1).

        Supports:
          - IMF-fixdate:  Sun, 06 Nov 1994 08:49:37 GMT
          - RFC 850:      Sunday, 06-Nov-94 08:49:37 GMT
          - asctime:      Sun Nov  6 08:49:37 1994
        """

        value = cls._strip_ows_str(value)

        # The two comma-bearing formats: IMF-fixdate (day-name "," SP day SP month SP 4-digit-year SP time SP GMT) and
        # RFC 850 (day-name "," SP DD-Mon-YY SP time SP GMT). They are told apart below by field count and the '-' in
        # the RFC-850 date. asctime (no comma) is handled in the else branch.
        if ',' in value:
            weekday_str, _, after_comma = value.partition(',')
            after_comma = cls._strip_ows_str(after_comma)
            parts = after_comma.split()

            if len(parts) == 3 and parts[2].upper() == 'GMT' and '-' in parts[0]:
                # RFC 850: DD-Mon-YY HH:MM:SS GMT. The day-name here is the full weekday name - but as with the IMF
                # day-name only the first three characters are cross-checked below, leniently accepting both full names
                # ('Sunday') and abbreviations ('Sun').
                date_pieces = parts[0].split('-')
                if len(date_pieces) != 3:
                    raise ValueError(f'Invalid date component: {parts[0]}')

                day = cls._date_int(date_pieces[0], 'day', 2, 2)
                month_str = date_pieces[1].lower()

                # Two-digit year (or, non-conforming but accepted, a four-digit one). int() leniency ('+4', '1_4', '9',
                # '994') previously produced silently different years.
                year_raw = cls._date_int(date_pieces[2], 'year', 2, 4)

                # RFC 7231: interpret two-digit years >= 50 as 19xx, < 50 as 20xx.
                if year_raw < 100:
                    year = year_raw + 1900 if year_raw >= 50 else year_raw + 2000
                else:
                    year = year_raw

                time_pieces = parts[1].split(':')
                if len(time_pieces) != 3:
                    raise ValueError(f'Invalid time component: {parts[1]}')

                hour = cls._date_int(time_pieces[0], 'hour', 2, 2)
                minute = cls._date_int(time_pieces[1], 'minute', 2, 2)
                second = cls._date_int(time_pieces[2], 'second', 2, 2)

                month = cls._MONTH_NAMES.get(month_str)
                if month is None:
                    raise ValueError(f'Invalid month: {month_str}')

                dt = datetime.datetime(year, month, day, hour, minute, second, tzinfo=datetime.timezone.utc)  # noqa
                cls._check_http_date_weekday(dt, weekday_str[:3])
                return dt

            elif len(parts) == 5 and parts[4].upper() == 'GMT':
                # IMF-fixdate: DD Mon YYYY HH:MM:SS GMT
                day = cls._date_int(parts[0], 'day', 2, 2)
                month_str = parts[1].lower()
                year = cls._date_int(parts[2], 'year', 4, 4)

                time_pieces = parts[3].split(':')
                if len(time_pieces) != 3:
                    raise ValueError(f'Invalid time component: {parts[3]}')

                hour = cls._date_int(time_pieces[0], 'hour', 2, 2)
                minute = cls._date_int(time_pieces[1], 'minute', 2, 2)
                second = cls._date_int(time_pieces[2], 'second', 2, 2)

                month = cls._MONTH_NAMES.get(month_str)
                if month is None:
                    raise ValueError(f'Invalid month: {month_str}')

                dt = datetime.datetime(year, month, day, hour, minute, second, tzinfo=datetime.timezone.utc)  # noqa
                cls._check_http_date_weekday(dt, weekday_str[:3])
                return dt

            raise ValueError(f'Cannot parse date: {value}')

        else:
            # asctime: Sun Nov  6 08:49:37 1994 (Strict fixed-width check)
            # 012345678901234567890123
            # Sun Nov  6 08:49:37 1994
            if len(value) != 24:
                raise ValueError(f'Invalid asctime length: {len(value)}')

            month_str = value[4:7].lower()
            # Handle the space-padded day (e.g., " 6")
            day_str = value[8:10].replace(' ', '0')
            day = cls._date_int(day_str, 'day', 2, 2)

            time_pieces = value[11:19].split(':')
            if len(time_pieces) != 3:
                raise ValueError('Invalid time component')

            hour = cls._date_int(time_pieces[0], 'hour', 2, 2)
            minute = cls._date_int(time_pieces[1], 'minute', 2, 2)
            second = cls._date_int(time_pieces[2], 'second', 2, 2)

            year = cls._date_int(value[20:24], 'year', 4, 4)
            month = cls._MONTH_NAMES.get(month_str)
            if month is None:
                raise ValueError(f'Invalid month: {month_str}')

            dt = datetime.datetime(year, month, day, hour, minute, second, tzinfo=datetime.timezone.utc)  # noqa
            cls._check_http_date_weekday(dt, value[:3])
            return dt

    def _prepare_date(self, headers: ParsedHttpHeaders, prepared: PreparedParsedHttpHeaders) -> None:
        if 'date' not in headers:
            return

        raw = headers['date']
        try:
            prepared.date = self._parse_http_date(raw)
        except (ValueError, IndexError, OverflowError) as e:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_DATE,
                message=f'Cannot parse Date header: {e}',
            ) from None

    def _prepare_cache_control(self, headers: ParsedHttpHeaders, prepared: PreparedParsedHttpHeaders) -> None:
        if 'cache-control' not in headers:
            return

        directives: ta.Dict[str, ta.Optional[str]] = {}

        for part in self._parse_comma_list(headers['cache-control']):
            eq_idx = part.find('=')
            if eq_idx < 0:
                # cache-directive is a token (RFC 7234 §5.2).
                if not self._is_token(part.lower()):
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_CACHE_CONTROL,
                        message=f'Cache-Control directive is not a valid token: {part!r}',
                    )

                if part.lower() in directives:
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_CACHE_CONTROL,
                        message=f'Duplicate Cache-Control directive: {part.lower()!r}',
                    )

                directives[part.lower()] = None
                continue

            name = self._strip_ows_str(part[:eq_idx]).lower()
            value = self._strip_ows_str(part[eq_idx + 1:])

            # cache-directive = token [ "=" ( token / quoted-string ) ] (RFC 7234 §5.2) - reject empty names.
            if not name:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_CACHE_CONTROL,
                    message=f'Cache-Control directive has an empty name: {part!r}',
                )

            # cache-directive is a token (RFC 7234 §5.2).
            if not self._is_token(name):
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_CACHE_CONTROL,
                    message=f'Cache-Control directive is not a valid token: {name!r}',
                )

            if value.startswith('"'):
                # A quoted-string that does not span exactly to the end (junk after the closing DQUOTE) is invalid -
                # junk following a quoted-string was previously silently dropped. Note: value is the OWS-stripped
                # remainder of the element, so strip the same OWS from the raw remainder before comparing offsets.
                try:
                    value, after_pos = self._parse_quoted_string(value, 0)
                except ValueError:
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_CACHE_CONTROL,
                        message=f'Invalid quoted-string in Cache-Control directive: {name}',
                    ) from None

                remainder = self._strip_ows_str(part[eq_idx + 1:])
                if remainder[after_pos:]:
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_CACHE_CONTROL,
                        message=f'Unexpected content after quoted Cache-Control value: {name!r}',
                    )

            else:
                # A bare directive value is a token (RFC 7234 §5.2) - previously any junk was kept verbatim.
                if not value or not self._is_token(value):
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_CACHE_CONTROL,
                        message=f'Cache-Control directive value is not a valid token: {value!r}',
                    )

            if name in directives:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_CACHE_CONTROL,
                    message=f'Duplicate Cache-Control directive: {name!r}',
                )

            directives[name] = value

        prepared.cache_control = directives

    def _prepare_accept_encoding(self, headers: ParsedHttpHeaders, prepared: PreparedParsedHttpHeaders) -> None:
        if 'accept-encoding' not in headers:
            return

        items: ta.List[PreparedParsedHttpHeaders.AcceptEncodingItem] = []

        for part in self._parse_comma_list(headers['accept-encoding']):
            try:
                coding, q, params = self._split_header_element(part)
            except ValueError:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_ACCEPT_ENCODING,
                    message=f'Invalid element in Accept-Encoding: {part!r}',
                ) from None

            # A truly empty element is ignorable per RFC 9110 §5.6.1, but an empty coding carrying parameters or a
            # qvalue is malformed and must not be silently dropped.
            if not coding:
                if params or q != 1.0:
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_ACCEPT_ENCODING,
                        message=f'Accept-Encoding element has an empty coding with parameters',
                    )
                continue

            # codings are tokens (RFC 9110 §12.5.3).
            if not self._is_token(coding):
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_ACCEPT_ENCODING,
                    message=f'Accept-Encoding coding is not a valid token: {coding!r}',
                )

            # Accept-Encoding codings take no parameters besides q (RFC 9110 §12.5.3: weight only).
            if params:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_ACCEPT_ENCODING,
                    message=f'Accept-Encoding coding has unexpected parameters: {part!r}',
                )

            items.append(PreparedParsedHttpHeaders.AcceptEncodingItem(
                coding=coding,
                q=q,
            ))

        # The header was present but contains no codings - 1#coding requires at least one.
        if not items:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_ACCEPT_ENCODING,
                message='Accept-Encoding header present but empty',
            )

        prepared.accept_encoding = items

    def _prepare_accept(self, headers: ParsedHttpHeaders, prepared: PreparedParsedHttpHeaders) -> None:
        if 'accept' not in headers:
            return

        items: ta.List[PreparedParsedHttpHeaders.AcceptItem] = []

        for part in self._parse_comma_list(headers['accept']):
            try:
                media_range, q, params = self._split_header_element(part)
            except ValueError:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_ACCEPT,
                    message=f'Invalid element in Accept: {part!r}',
                ) from None

            # A truly empty element is ignorable per RFC 9110 §5.6.1, but an empty media-range carrying parameters or a
            # qvalue is malformed and must not be silently dropped.
            if not media_range:
                if params or q != 1.0:
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_ACCEPT,
                        message='Accept element has an empty media-range with parameters',
                    )
                continue

            # media-range = "*/*" / ( type "/*" ) / ( type "/" subtype ) - type and subtype are tokens, with '*' only
            # legal as the complete type of "*/*" or the complete subtype of "type/*" (RFC 9110 §12.5.1).
            type_, _, subtype = media_range.partition('/')
            if not type_ or not subtype:
                raise SemanticHeaderHttpParseError(
                    code=SemanticHeaderHttpParseErrorCode.INVALID_ACCEPT,
                    message=f'Accept media-range is not a valid type/subtype pair: {media_range!r}',
                )

            for part in (type_, subtype):
                if part == '*':
                    continue
                if not self._is_token(part) or '*' in part:
                    raise SemanticHeaderHttpParseError(
                        code=SemanticHeaderHttpParseErrorCode.INVALID_ACCEPT,
                        message=f'Accept media-range is not a valid type/subtype pair: {media_range!r}',
                    )

            items.append(PreparedParsedHttpHeaders.AcceptItem(
                media_range=media_range,
                q=q,
                params=params,
            ))

        # The header was present but contains no media-ranges - 1#media-range requires at least one.
        if not items:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_ACCEPT,
                message='Accept header present but empty',
            )

        prepared.accept = items

    def _prepare_authorization(self, headers: ParsedHttpHeaders, prepared: PreparedParsedHttpHeaders) -> None:
        values = headers.get_all('authorization')
        if not values:
            return

        if len(values) > 1:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.MULTIPLE_AUTHORIZATION_HEADERS,
                message=f'Multiple Authorization headers found ({len(values)})',
            )

        raw = self._strip_ows_str(values[0])
        if not raw:
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_AUTHORIZATION,
                message='Authorization header is present but empty',
            )

        # credentials = auth-scheme [ 1*SP ( token68 / [ ( "," / auth-param ) *( OWS "," / OWS auth-param ) ] ) ] - the
        # separator is 1*SP (never HTAB), and auth-scheme must be a token (RFC 7235). Consume ALL the separating SPs so
        # a value like 'Basic  dXNlcg==' does not leave a stray leading SP in the credentials - downstream
        # token68/base64 consumers would see a different value than peers that trim it.
        sp_idx = raw.find(' ')
        if sp_idx < 0:
            scheme = raw
            credentials = ''
        else:
            scheme = raw[:sp_idx]
            credentials = raw[sp_idx + 1:].lstrip(' ')

        if not scheme or not self._is_token(scheme):
            raise SemanticHeaderHttpParseError(
                code=SemanticHeaderHttpParseErrorCode.INVALID_AUTHORIZATION,
                message=f'Authorization auth-scheme is not a valid token: {scheme!r}',
            )

        prepared.authorization = PreparedParsedHttpHeaders.AuthorizationValue(
            scheme=scheme,
            credentials=credentials,
        )


##


def parse_http_message(
        data: Bytes,
        mode: HttpParser.Mode = HttpParser.Mode.AUTO,
        config: ta.Optional[HttpParser.Config] = None,
) -> ParsedHttpMessage:
    parser = HttpParser(**(dict(config=config) if config is not None else {}))
    return parser.parse_message(data, mode=mode)


def parse_http_trailers(
        data: Bytes,
        config: ta.Optional[HttpParser.Config] = None,
) -> ParsedHttpTrailers:
    parser = HttpParser(**(dict(config=config) if config is not None else {}))
    return parser.parse_trailers(data)
