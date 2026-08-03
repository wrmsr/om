# ruff: noqa: UP006 UP007 UP037 UP043 UP045
# @om-lite
import dataclasses as dc
import typing as ta

from ..headers import HttpHeaders


##


def is_chunked_transfer_encoding(headers: HttpHeaders) -> bool:
    """
    Whether a message is framed with the chunked transfer-coding.

    Transfer-Encoding is a `#`-list, so `gzip, chunked` is chunked-framed - but RFC 9112 §6.1 requires `chunked` to be
    the final coding, so `chunked, gzip` is not (the parser rejects such messages outright, but these headers are also
    built by hand outbound).
    """

    if not headers.contains_list_value('transfer-encoding', 'chunked', ignore_case=True):
        return False

    last = ''
    for v in headers.lower['transfer-encoding']:
        for e in v.split(','):
            e = e.strip()
            if e:
                last = e

    return last == 'chunked'


##


@dc.dataclass()
class IoPipelineHttpBodyModeError(Exception):
    reason: str


@ta.final
@dc.dataclass(frozen=True)
class IoPipelineHttpBodyMode:
    mode: ta.Literal['empty', 'eof', 'cl', 'chunked', 'tunnel']
    length: ta.Optional[int]

    @classmethod
    def select(
            cls,
            headers: HttpHeaders,
            *,
            if_length_missing: ta.Literal['empty', 'eof'],
    ) -> 'IoPipelineHttpBodyMode':
        if 'transfer-encoding' in headers and 'content-length' in headers:
            raise IoPipelineHttpBodyModeError('both Transfer-Encoding and Content-Length are present')

        if is_chunked_transfer_encoding(headers):
            return cls('chunked', None)

        cl = headers.single.get('content-length')
        if not cl:
            return cls(if_length_missing, None)

        try:
            n = int(cl)
        except ValueError:
            raise IoPipelineHttpBodyModeError('bad Content-Length') from None

        if n < 0:
            raise IoPipelineHttpBodyModeError('bad Content-Length')

        if n == 0:
            return cls('empty', None)

        return cls('cl', n)
