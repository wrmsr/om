# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
https://docs.aws.amazon.com/IAM/latest/UserGuide/create-signed-request.html
https://docs.aws.amazon.com/AmazonS3/latest/API/sigv4-streaming.html

TODO:
 - secrets
"""
import dataclasses as dc
import datetime
import hashlib
import hmac
import typing as ta
import urllib.parse

from omcore.lite.check import check


##


class AwsSigner:
    def __init__(
            self,
            creds: 'AwsSigner.Credentials',
            region_name: str,
            service_name: str,
    ) -> None:
        super().__init__()

        self._creds = creds
        self._region_name = region_name
        self._service_name = service_name

    #

    @dc.dataclass(frozen=True)
    class Credentials:
        access_key_id: str
        secret_access_key: str = dc.field(repr=False)
        session_token: ta.Optional[str] = dc.field(default=None, repr=False)

    @dc.dataclass(frozen=True)
    class Request:
        method: str
        url: str
        headers: ta.Mapping[str, ta.Sequence[str]] = dc.field(default_factory=dict)
        payload: bytes = b''

    #

    ISO8601 = '%Y%m%dT%H%M%SZ'

    #

    @staticmethod
    def _host_from_url(url: str) -> str:
        url_parts = urllib.parse.urlsplit(url)
        host = check.non_empty_str(url_parts.hostname)
        default_ports = {
            'http': 80,
            'https': 443,
        }
        if url_parts.port is not None:
            if url_parts.port != default_ports.get(url_parts.scheme):
                host = f'{host}:{int(url_parts.port)}'
        return host

    @staticmethod
    def _lower_case_http_map(d: ta.Mapping[str, ta.Sequence[str]]) -> ta.Mapping[str, ta.Sequence[str]]:
        o: ta.Dict[str, ta.List[str]] = {}
        for k, vs in d.items():
            o.setdefault(k.lower(), []).extend(check.not_isinstance(vs, str))
        return o

    #

    UNSIGNED_PAYLOAD = 'UNSIGNED-PAYLOAD'
    STREAMING_PAYLOAD = 'STREAMING-AWS4-HMAC-SHA256-PAYLOAD'

    _URI_UNRESERVED = frozenset(b'ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789-_.~')

    @classmethod
    def uri_encode(cls, s: str, *, encode_slash: bool) -> str:
        """
        AWS's UriEncode: every byte of the UTF-8 encoding outside the unreserved set becomes an uppercase %XX, with '/'
        left alone only when encode_slash is false. URLs sent to AWS should be built with exactly this encoding so the
        wire form and the canonical form coincide.
        """

        out: ta.List[str] = []
        for b in s.encode('utf-8'):
            if b in cls._URI_UNRESERVED or (b == 0x2f and not encode_slash):
                out.append(chr(b))
            else:
                out.append(f'%{b:02X}')
        return ''.join(out)

    @staticmethod
    def _remove_dot_segments(path: str) -> str:
        """RFC 3986 section 5.2.4, plus collapsing of repeated slashes, as AWS services other than S3 require."""

        if not path:
            return ''
        out: ta.List[str] = []
        for seg in path.split('/'):
            if not seg or seg == '.':
                continue
            if seg == '..':
                if out:
                    out.pop()
            else:
                out.append(seg)
        first = '/' if path[0] == '/' else ''
        last = '/' if path[-1] == '/' and out else ''
        return first + '/'.join(out) + last

    @staticmethod
    def _as_bytes(data: ta.Union[str, bytes]) -> bytes:
        return data if isinstance(data, bytes) else data.encode('utf-8')

    @classmethod
    def _sha256(cls, data: ta.Union[str, bytes]) -> str:
        return hashlib.sha256(cls._as_bytes(data)).hexdigest()

    @classmethod
    def _sha256_sign(cls, key: bytes, msg: ta.Union[str, bytes]) -> bytes:
        return hmac.new(key, cls._as_bytes(msg), hashlib.sha256).digest()

    @classmethod
    def _sha256_sign_hex(cls, key: bytes, msg: ta.Union[str, bytes]) -> str:
        return hmac.new(key, cls._as_bytes(msg), hashlib.sha256).hexdigest()

    _EMPTY_SHA256: str

    #

    _SIGNED_HEADERS_BLACKLIST = frozenset([
        'authorization',
        'expect',
        'user-agent',
        'x-amzn-trace-id',
    ])

    def _validate_request(self, req: Request) -> None:
        check.non_empty_str(req.method)
        check.equal(req.method.upper(), req.method)
        for k, vs in req.headers.items():
            check.equal(k.strip(), k)
            for v in vs:
                check.equal(v.strip(), v)

    #

    def _canonical_uri(self, path: str) -> str:
        """
        Re-encodes each path segment canonically, so '%2F' within a segment survives. S3 encodes once and never
        normalizes. Every other service normalizes the path and then encodes the already-encoded path again.
        """

        if not path:
            path = '/'
        if self._service_name != 's3':
            path = self._remove_dot_segments(path) or '/'
        enc = '/'.join(self.uri_encode(urllib.parse.unquote(s), encode_slash=True) for s in path.split('/'))
        if self._service_name == 's3':
            return enc
        return self.uri_encode(enc, encode_slash=False)

    @classmethod
    def _canonical_query(cls, query: str) -> str:
        # Deliberately urllib.parse.unquote rather than unquote_plus / parse_qsl, which would turn '+' into a space.
        pairs: ta.List[ta.Tuple[str, str]] = []
        for part in query.split('&'):
            if not part:
                continue
            k, _, v = part.partition('=')
            pairs.append((
                cls.uri_encode(urllib.parse.unquote(k), encode_slash=True),
                cls.uri_encode(urllib.parse.unquote(v), encode_slash=True),
            ))
        return '&'.join(f'{k}={v}' for k, v in sorted(pairs))

    @staticmethod
    def _canonical_header_value(v: str) -> str:
        return ' '.join(v.split())


AwsSigner._EMPTY_SHA256 = AwsSigner._sha256(b'')  # noqa


##


class V4AwsChunkSigner:
    """
    Signs the chunks of an aws-chunked (STREAMING-AWS4-HMAC-SHA256-PAYLOAD) body, each chained to the previous chunk's
    signature, starting from the seed request's. Every chunk but the last must be exactly chunk_size bytes - which is
    what the precomputed Content-Length assumed - and chunk_size must be at least 8KiB.
    """

    MIN_CHUNK_SIZE: ta.ClassVar[int] = 8 * 1024

    def __init__(
            self,
            *,
            signing_key: bytes,
            req_dt: str,
            scope: str,
            seed_signature: str,
            decoded_length: int,
            chunk_size: int,
    ) -> None:
        super().__init__()

        self._signing_key = signing_key
        self._req_dt = req_dt
        self._scope = scope
        self._prev_signature = seed_signature
        self._decoded_length = decoded_length
        self._chunk_size = chunk_size

        self._sent = 0
        self._finished = False

    @property
    def decoded_length(self) -> int:
        return self._decoded_length

    @property
    def chunk_size(self) -> int:
        return self._chunk_size

    def _sign(self, data: bytes) -> str:
        sts = '\n'.join([
            'AWS4-HMAC-SHA256-PAYLOAD',
            self._req_dt,
            self._scope,
            self._prev_signature,
            AwsSigner._EMPTY_SHA256,  # noqa
            AwsSigner._sha256(data),  # noqa
        ])
        sig = AwsSigner._sha256_sign_hex(self._signing_key, sts)  # noqa
        self._prev_signature = sig
        return sig

    def sign_chunk(self, data: bytes) -> bytes:
        """Returns the framed chunk: `<hex length>;chunk-signature=<signature>\\r\\n<data>\\r\\n`."""

        check.state(not self._finished)
        n = len(data)
        if not n:
            raise ValueError('empty data chunk - use final_chunk')
        if self._sent + n > self._decoded_length:
            raise ValueError('chunks exceed decoded length')
        if n != self._chunk_size and self._sent + n != self._decoded_length:
            raise ValueError(f'only the last chunk may differ from the chunk size: {n}')
        if n > self._chunk_size:
            raise ValueError(f'chunk larger than the chunk size: {n}')
        sig = self._sign(data)
        self._sent += n
        return b''.join([f'{n:x};chunk-signature={sig}\r\n'.encode('ascii'), data, b'\r\n'])

    def final_chunk(self) -> bytes:
        check.state(not self._finished)
        if self._sent != self._decoded_length:
            raise ValueError(f'sent {self._sent} of {self._decoded_length} bytes')
        self._finished = True
        sig = self._sign(b'')
        return f'0;chunk-signature={sig}\r\n\r\n'.encode('ascii')


def _aws_chunk_overhead(n: int) -> int:
    return len(f'{n:x}') + len(';chunk-signature=') + 64 + 4


def aws_chunked_encoded_length(decoded_length: int, chunk_size: int) -> int:
    full, rem = divmod(decoded_length, chunk_size)
    total = full * (_aws_chunk_overhead(chunk_size) + chunk_size)
    if rem:
        total += _aws_chunk_overhead(rem) + rem
    return total + _aws_chunk_overhead(0)


def aws_chunked_encode(data: bytes, *, signer: V4AwsChunkSigner) -> bytes:
    """Encodes a whole in-memory body - for tests and small bodies."""

    cs = signer.chunk_size
    return b''.join([
        *[signer.sign_chunk(data[i:i + cs]) for i in range(0, len(data), cs)],
        signer.final_chunk(),
    ])


##


class V4AwsSigner(AwsSigner):
    @dc.dataclass(frozen=True)
    class _Signed:
        headers: ta.Mapping[str, ta.Sequence[str]]
        canonical_request: str
        signature: str
        req_dt: str
        scope: str
        signing_key: bytes

    def _sign(
            self,
            req: AwsSigner.Request,
            *,
            payload_hash: str,
            emit_content_sha256: bool,
            extra_headers: ta.Optional[ta.Mapping[str, ta.Sequence[str]]] = None,
            utcnow: ta.Optional[datetime.datetime] = None,
    ) -> _Signed:
        self._validate_request(req)

        #

        if utcnow is None:
            utcnow = datetime.datetime.now(tz=datetime.timezone.utc)  # noqa
        req_dt = utcnow.strftime(self.ISO8601)

        #

        parsed_url = urllib.parse.urlsplit(req.url)
        canon_uri = self._canonical_uri(parsed_url.path)
        canon_qs = self._canonical_query(parsed_url.query)

        #

        headers_to_sign: ta.Dict[str, ta.List[str]] = {
            k: list(v)
            for k, v in self._lower_case_http_map(req.headers).items()
            if k not in self._SIGNED_HEADERS_BLACKLIST
        }

        if extra_headers:
            for k, v in self._lower_case_http_map(extra_headers).items():
                headers_to_sign[k] = list(v)

        if 'host' not in headers_to_sign:
            headers_to_sign['host'] = [self._host_from_url(req.url)]

        headers_to_sign['x-amz-date'] = [req_dt]

        if emit_content_sha256:
            headers_to_sign['x-amz-content-sha256'] = [payload_hash]

        if (token := self._creds.session_token) is not None:
            headers_to_sign['x-amz-security-token'] = [token]

        sorted_header_names = sorted(headers_to_sign)
        canon_headers = ''.join([
            k + ':' + ','.join(self._canonical_header_value(v) for v in headers_to_sign[k]) + '\n'
            for k in sorted_header_names
        ])
        signed_headers = ';'.join(sorted_header_names)

        #

        canon_req = '\n'.join([
            req.method,
            canon_uri,
            canon_qs,
            canon_headers,
            signed_headers,
            payload_hash,
        ])

        #

        algorithm = 'AWS4-HMAC-SHA256'
        scope_parts = [
            req_dt[:8],
            self._region_name,
            self._service_name,
            'aws4_request',
        ]
        scope = '/'.join(scope_parts)
        hashed_canon_req = self._sha256(canon_req)
        string_to_sign = '\n'.join([
            algorithm,
            req_dt,
            scope,
            hashed_canon_req,
        ])

        #

        key = self._creds.secret_access_key
        key_date = self._sha256_sign(f'AWS4{key}'.encode('utf-8'), req_dt[:8])  # noqa
        key_region = self._sha256_sign(key_date, self._region_name)
        key_service = self._sha256_sign(key_region, self._service_name)
        key_signing = self._sha256_sign(key_service, 'aws4_request')
        sig = self._sha256_sign_hex(key_signing, string_to_sign)

        #

        cred_scope = '/'.join([
            self._creds.access_key_id,
            *scope_parts,
        ])
        auth = f'{algorithm} ' + ', '.join([
            f'Credential={cred_scope}',
            f'SignedHeaders={signed_headers}',
            f'Signature={sig}',
        ])

        #

        out = {
            'Authorization': [auth],
            'X-Amz-Date': [req_dt],
        }
        if emit_content_sha256:
            out['X-Amz-Content-SHA256'] = [payload_hash]
        if token is not None:
            out['X-Amz-Security-Token'] = [token]

        return V4AwsSigner._Signed(
            headers=out,
            canonical_request=canon_req,
            signature=sig,
            req_dt=req_dt,
            scope=scope,
            signing_key=key_signing,
        )

    def sign(
            self,
            req: AwsSigner.Request,
            *,
            sign_payload: bool = False,
            payload_hash: ta.Optional[str] = None,
            utcnow: ta.Optional[datetime.datetime] = None,
    ) -> ta.Mapping[str, ta.Sequence[str]]:
        """
        Returns the headers to add to the request. With sign_payload, or an explicit payload_hash (such as
        UNSIGNED_PAYLOAD), x-amz-content-sha256 is signed and returned - which S3 requires.
        """

        if payload_hash is None:
            payload_hash = self._sha256(req.payload) if req.payload else self._EMPTY_SHA256
            emit = sign_payload
        else:
            emit = True

        return self._sign(
            req,
            payload_hash=payload_hash,
            emit_content_sha256=emit,
            utcnow=utcnow,
        ).headers

    def sign_streaming(
            self,
            req: AwsSigner.Request,
            *,
            decoded_length: int,
            chunk_size: int,
            utcnow: ta.Optional[datetime.datetime] = None,
    ) -> ta.Tuple[ta.Mapping[str, ta.Sequence[str]], V4AwsChunkSigner]:
        """
        Signs the seed request of an aws-chunked upload, returning the headers to add - including Content-Encoding,
        Content-Length, and X-Amz-Decoded-Content-Length - and the signer for the body's chunks.
        """

        if req.payload:
            raise ValueError('streaming requests carry no payload - the body is produced by the chunk signer')
        if chunk_size < V4AwsChunkSigner.MIN_CHUNK_SIZE:
            raise ValueError(f'chunk size must be at least {V4AwsChunkSigner.MIN_CHUNK_SIZE}: {chunk_size}')

        encoded_length = aws_chunked_encoded_length(decoded_length, chunk_size)

        lh = self._lower_case_http_map(req.headers)
        content_encoding = ','.join(['aws-chunked', *lh.get('content-encoding', [])])

        extra = {
            'Content-Encoding': [content_encoding],
            'Content-Length': [str(encoded_length)],
            'X-Amz-Decoded-Content-Length': [str(decoded_length)],
        }

        signed = self._sign(
            req,
            payload_hash=self.STREAMING_PAYLOAD,
            emit_content_sha256=True,
            extra_headers=extra,
            utcnow=utcnow,
        )

        return (
            {**signed.headers, **extra},
            V4AwsChunkSigner(
                signing_key=signed.signing_key,
                req_dt=signed.req_dt,
                scope=signed.scope,
                seed_signature=signed.signature,
                decoded_length=decoded_length,
                chunk_size=chunk_size,
            ),
        )
