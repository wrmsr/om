import typing as ta

from omcore import dataclasses as dc
from omcore.http import all as http

from ..streaming import S3StreamingSender


##


class BufferingStreamingSender(S3StreamingSender):
    """
    Stands in for real streaming request bodies until omcore.http has them: drains the aws-chunked body into memory
    and sends it through the ordinary request path, aws-chunked headers and all.
    """

    def __init__(self) -> None:
        super().__init__()

        self.sent: list[http.HttpClientRequest] = []

    async def send(
            self,
            client: http.AsyncHttpClient,
            request: http.HttpClientRequest,
            body: ta.AsyncIterable[bytes],
    ) -> http.HttpClientResponse:
        buf = b''.join([b async for b in body])
        req = dc.replace(request, data=buf)
        self.sent.append(req)
        return await client.request(req)
