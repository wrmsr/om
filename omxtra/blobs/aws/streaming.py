"""
Streamed uploads: aws-chunked bodies with per-chunk SigV4 signatures, sent without buffering the payload in memory.

omcore.http request bodies cannot stream yet, so everything here stops at one seam - S3StreamingSender - whose default
implementation raises NotImplementedError. Tests substitute a sender which buffers the encoded body and sends it through
the ordinary request path.
"""
import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore.http import all as http
from ominfra.clouds.aws import auth as aws_auth


##


@dc.dataclass(frozen=True)
class S3StreamBody:
    source: ta.AsyncIterable[bytes]
    length: int


async def aws_chunked_body(
        source: ta.AsyncIterable[bytes],
        *,
        chunk_signer: aws_auth.V4AwsChunkSigner,
) -> ta.AsyncIterator[bytes]:
    """
    Re-blocks the source into the signer's chunk size and yields framed, signed chunks followed by the final chunk.
    Raises if the source yields more or fewer bytes than the signer's decoded length.
    """

    cs = chunk_signer.chunk_size
    n = chunk_signer.decoded_length
    buf = bytearray()
    seen = 0
    async for data in source:
        seen += len(data)
        if seen > n:
            raise ValueError(f'source exceeded its declared length of {n} bytes')
        buf.extend(data)
        # A full chunk is always valid, last or not - only a short one must be the last.
        while len(buf) >= cs:
            yield chunk_signer.sign_chunk(bytes(buf[:cs]))
            del buf[:cs]
    if seen != n:
        raise ValueError(f'source yielded {seen} bytes, declared {n}')
    if buf:
        yield chunk_signer.sign_chunk(bytes(buf))
    yield chunk_signer.final_chunk()


##


class S3StreamingSender(lang.Abstract):
    @abc.abstractmethod
    def send(
            self,
            client: http.AsyncHttpClient,
            request: http.HttpClientRequest,
            body: ta.AsyncIterable[bytes],
    ) -> ta.Awaitable[http.HttpClientResponse]:
        """
        Sends a request whose data is None - its Content-Length and aws-chunked headers already set and signed - with
        the given body.
        """

        raise NotImplementedError


class HttpClientStreamingSender(S3StreamingSender):
    async def send(
            self,
            client: http.AsyncHttpClient,
            request: http.HttpClientRequest,
            body: ta.AsyncIterable[bytes],
    ) -> http.HttpClientResponse:
        # TODO: omcore.http request bodies cannot stream yet. Once HttpClientRequest.data accepts an
        #  AsyncIterable[bytes] (with an explicit Content-Length, never chunked transfer encoding), this becomes:
        #
        #      return await client.request(dc.replace(request, data=body))
        #
        raise NotImplementedError('streaming request bodies are not yet supported by omcore.http')
