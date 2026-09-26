import enum
import socket
import typing as ta

from ... import blobs
from .restxml import RestXmlError


##


class S3ResponseError(blobs.BlobStoreError):
    """An S3 error response not mapped to a more specific blob error."""

    def __init__(
            self,
            *,
            status: int,
            code: str | None = None,
            message: str | None = None,
            request_id: str | None = None,
            host_id: str | None = None,
            op: str | None = None,
            after_ambiguous: bool = False,
    ) -> None:
        super().__init__(status, code, message)

        self._status = status
        self._code = code
        self._message = message
        self._request_id = request_id
        self._host_id = host_id
        self._op = op
        self._after_ambiguous = after_ambiguous

    @classmethod
    def of(cls, e: RestXmlError, *, op: str | None = None, after_ambiguous: bool = False) -> S3ResponseError:
        return cls(
            status=e.status,
            code=e.code,
            message=e.message,
            request_id=e.request_id,
            host_id=e.host_id,
            op=op,
            after_ambiguous=after_ambiguous,
        )

    def __str__(self) -> str:
        return f'{self._op or "request"} failed: {self._status} {self._code or ""} {self._message or ""}'.strip()

    @property
    def status(self) -> int:
        return self._status

    @property
    def code(self) -> str | None:
        return self._code

    @property
    def message(self) -> str | None:
        return self._message

    @property
    def request_id(self) -> str | None:
        return self._request_id

    @property
    def host_id(self) -> str | None:
        return self._host_id

    @property
    def after_ambiguous(self) -> bool:
        """Whether an earlier, retried attempt of the same request may have taken effect."""

        return self._after_ambiguous


##


def is_error_body(body: bytes) -> bool:
    """
    Detects an <Error> document, which CopyObject, CompleteMultipartUpload, and UploadPartCopy can return with a 200
    status after the request has been accepted.
    """

    s = body.lstrip()
    if s.startswith(b'<?xml'):
        s = s[s.find(b'?>') + 2:].lstrip() if b'?>' in s else s
    return s.startswith((b'<Error>', b'<Error '))


class S3FailureKind(enum.Enum):
    READ_FAILED = enum.auto()  # a read failed; retrying is safe
    NOT_APPLIED = enum.auto()  # known not to have taken effect (409 conflict, refused connection)
    THROTTLED = enum.auto()  # 503 SlowDown
    AMBIGUOUS = enum.auto()  # a write which may or may not have taken effect
    TERMINAL = enum.auto()  # retrying will not help


def classify_status(status: int, code: str | None, *, read: bool) -> S3FailureKind:
    if status == 503 and code == 'SlowDown':
        return S3FailureKind.THROTTLED
    if status == 409 and code == 'ConditionalRequestConflict':
        return S3FailureKind.NOT_APPLIED
    if status >= 500 and status != 501:
        return S3FailureKind.READ_FAILED if read else S3FailureKind.AMBIGUOUS
    return S3FailureKind.TERMINAL


_NOT_SENT_ERRORS: tuple[type[BaseException], ...] = (
    ConnectionRefusedError,
    socket.gaierror,
)


def _causes(e: BaseException) -> ta.Iterator[BaseException]:
    seen: set[int] = set()
    cur: BaseException | None = e
    while cur is not None and id(cur) not in seen:
        seen.add(id(cur))
        yield cur
        cur = cur.__cause__ or cur.__context__


def classify_transport_error(e: BaseException, *, read: bool) -> S3FailureKind:
    """Only failures which provably happened before anything was sent are NOT_APPLIED - everything else may have."""

    if any(isinstance(c, _NOT_SENT_ERRORS) for c in _causes(e)):
        return S3FailureKind.NOT_APPLIED
    return S3FailureKind.READ_FAILED if read else S3FailureKind.AMBIGUOUS
