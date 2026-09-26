import re
import typing as ta
import urllib.parse

from omcore import dataclasses as dc
from ominfra.clouds.aws import auth as aws_auth

from .restxml import RestXmlRequest


##


_VIRTUAL_HOSTABLE_BUCKET_PAT = re.compile(r'[a-z0-9][a-z0-9-]{1,61}[a-z0-9]')


@dc.dataclass(frozen=True, kw_only=True)
class S3Endpoint:
    """
    Path-style addressing (the default) works on AWS, R2, and s3mock alike. Virtual-hosted addressing puts the bucket in
    the host name, and needs a DNS-compatible bucket name without dots.
    """

    url: str  # scheme://host[:port], no path
    region: str
    virtual_hosted: bool = False

    def __post_init__(self) -> None:
        p = urllib.parse.urlsplit(self.url)
        if p.scheme not in ('http', 'https') or not p.hostname:
            raise ValueError(f'bad endpoint url: {self.url!r}')
        if p.path not in ('', '/') or p.query or p.fragment:
            raise ValueError(f'endpoint url must not have a path: {self.url!r}')

    @property
    def is_https(self) -> bool:
        return self.url.startswith('https:')


def check_bucket_addressable(endpoint: S3Endpoint, bucket: str) -> None:
    if not bucket or '/' in bucket:
        raise ValueError(f'bad bucket name: {bucket!r}')
    if endpoint.virtual_hosted and not _VIRTUAL_HOSTABLE_BUCKET_PAT.fullmatch(bucket):
        raise ValueError(f'bucket name not usable with virtual-hosted addressing: {bucket!r}')


def encode_query(pairs: ta.Iterable[tuple[str, str | None]]) -> str:
    """Encodes and sorts exactly as the signer canonicalizes, so the wire and canonical forms coincide."""

    def e(s: str) -> str:
        return aws_auth.aws_uri_encode(s, encode_slash=True)

    enc = sorted((e(k), None if v is None else e(v)) for k, v in pairs)
    return '&'.join(k if v is None else f'{k}={v}' for k, v in enc)


def build_url(endpoint: S3Endpoint, bucket: str, rx: RestXmlRequest) -> tuple[str, str]:
    """Returns the url and the Host header value."""

    p = urllib.parse.urlsplit(endpoint.url)
    host = p.netloc
    path = rx.path
    if endpoint.virtual_hosted:
        host = f'{bucket}.{host}'
        bp = '/' + aws_auth.aws_uri_encode(bucket, encode_slash=True)
        if not (path == bp or path.startswith(bp + '/')):
            raise ValueError(f'request path does not start with the bucket: {path!r}')
        path = path[len(bp):] or '/'
    q = encode_query(rx.query)
    return f'{p.scheme}://{host}{path}' + (f'?{q}' if q else ''), host
