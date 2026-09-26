import base64
import datetime
import hashlib
import typing as ta

from omcore.http import all as http
from ominfra.clouds.aws import auth as aws_auth


##


class S3RequestSigner:
    """Turns a built S3 request into a signed HttpClientRequest."""

    def __init__(
            self,
            credentials: aws_auth.AwsSigner.Credentials,
            region: str,
            *,
            clock: ta.Callable[[], datetime.datetime] | None = None,
    ) -> None:
        super().__init__()

        self._signer = aws_auth.V4AwsSigner(credentials, region, 's3')
        self._clock = clock

    def _now(self) -> datetime.datetime | None:
        return self._clock() if self._clock is not None else None

    @staticmethod
    def _header_map(
            *,
            host: str,
            headers: ta.Iterable[tuple[str, str]],
            extra: ta.Iterable[tuple[str, str]],
    ) -> dict[str, list[str]]:
        """Later headers replace earlier ones of the same name, case-insensitively."""

        out: dict[str, list[str]] = {}
        names: dict[str, str] = {}
        for k, v in [('Host', host), *headers, *extra]:
            if (prev := names.get(k.lower())) is not None:
                del out[prev]
            names[k.lower()] = k
            out[k] = [v]
        return out

    def sign(
            self,
            *,
            method: str,
            url: str,
            host: str,
            headers: ta.Sequence[tuple[str, str]] = (),
            body: bytes | None = None,
            xml_body: bool = False,
            content_md5: bool = False,
            unsigned_payload: bool = False,
            timeout_s: float | None = None,
            no_decompress: bool = False,
    ) -> http.HttpClientRequest:
        extra: list[tuple[str, str]] = []
        if body is not None or method in ('PUT', 'POST'):
            # Set explicitly even when zero: some clients omit it for empty bodies, and S3 answers 411.
            extra.append(('Content-Length', str(len(body or b''))))
        if xml_body and body:
            extra.append(('Content-Type', 'application/xml'))
        if content_md5:
            extra.append(('Content-MD5', base64.b64encode(hashlib.md5(body or b'').digest()).decode('ascii')))  # noqa

        hm = self._header_map(host=host, headers=headers, extra=extra)

        req = aws_auth.AwsSigner.Request(method=method, url=url, headers=hm, payload=body or b'')
        if unsigned_payload and url.startswith('https:'):
            sig = self._signer.sign(req, payload_hash=aws_auth.UNSIGNED_PAYLOAD, utcnow=self._now())
        else:
            sig = self._signer.sign(req, sign_payload=True, utcnow=self._now())

        return http.HttpClientRequest(
            url,
            method,
            headers={**hm, **sig},
            data=body,
            timeout_s=timeout_s,
            no_decompress=no_decompress,
        )

    def sign_streaming(
            self,
            *,
            method: str,
            url: str,
            host: str,
            headers: ta.Sequence[tuple[str, str]] = (),
            decoded_length: int,
            chunk_size: int,
            timeout_s: float | None = None,
    ) -> tuple[http.HttpClientRequest, aws_auth.V4AwsChunkSigner]:
        """Returns the seed request - with no data, the body to be produced by the chunk signer - and the signer."""

        hm = self._header_map(host=host, headers=headers, extra=())
        req = aws_auth.AwsSigner.Request(method=method, url=url, headers=hm)
        sig, chunk_signer = self._signer.sign_streaming(
            req,
            decoded_length=decoded_length,
            chunk_size=chunk_size,
            utcnow=self._now(),
        )
        return http.HttpClientRequest(
            url,
            method,
            headers={**hm, **sig},
            timeout_s=timeout_s,
        ), chunk_signer
