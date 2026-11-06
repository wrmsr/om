"""
Test support: the web frontend serving for real, on an ephemeral port, over a scripted model - and a client for it,
speaking http over `omcore`'s own pipeline client.
"""
import contextlib
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import inject as inj
from omcore.formats.json import all as json
from omcore.http.clients.base import HttpClientRequest
from omcore.http.clients.pipelines.asyncio import AsyncioIoPipelineAsyncHttpClient

from .... import agent as agn
from ....core.http.sse import Utf8SseDecoder
from ..config import WebConfig
from ..main import RunningWeb
from ..main import running_web
from ..server.security import TOKEN_HEADER


##


@dc.dataclass(frozen=True, kw_only=True)
class WebTestResponse:
    status: int
    headers: ta.Mapping[str, str]
    body: bytes

    def json(self) -> ta.Any:
        return json.loads(self.body.decode('utf-8'))


class WebTestClient:
    def __init__(
            self,
            client: AsyncioIoPipelineAsyncHttpClient,
            base_url: str,
            token: str | None,
    ) -> None:
        super().__init__()

        self._client = client
        self._base_url = base_url.rstrip('/')
        self._token = token

    def _request(
            self,
            method: str,
            path: str,
            body: ta.Any = None,
            *,
            headers: ta.Mapping[str, str] | None = None,
    ) -> HttpClientRequest:
        hs: dict[str, str] = {}
        if self._token is not None:
            hs[TOKEN_HEADER.decode()] = self._token
        if body is not None:
            hs['content-type'] = 'application/json'
        hs.update(headers or {})

        return HttpClientRequest(
            self._base_url + path,
            method,
            headers=hs,
            data=json.dumps_compact(body).encode() if body is not None else None,
            timeout_s=30.,
        )

    def without_token(self) -> WebTestClient:
        """A client like this one, but for a page which never got the session's token."""

        return WebTestClient(self._client, self._base_url, None)

    async def request(
            self,
            method: str,
            path: str,
            body: ta.Any = None,
            *,
            headers: ta.Mapping[str, str] | None = None,
    ) -> WebTestResponse:
        async with (await self._client.stream_request(self._request(method, path, body, headers=headers))) as resp:
            data = await check.not_none(resp.stream).read()

            return WebTestResponse(
                status=resp.status,
                headers={k.lower(): v for k, v in (resp.headers.all if resp.headers else [])},
                body=bytes(data),
            )

    async def stream(
            self,
            method: str,
            path: str,
            body: ta.Any = None,
    ) -> ta.AsyncIterator[dict[str, ta.Any]]:
        """The feed entries of an sse response, as they arrive. Raises for a response which is not a 200."""

        async with (await self._client.stream_request(self._request(method, path, body))) as resp:
            if resp.status != 200:
                raise WebTestStreamError(resp.status, bytes(await check.not_none(resp.stream).read()))

            decoder = Utf8SseDecoder()
            stream = check.not_none(resp.stream)

            while data := await stream.read1():
                for ev in decoder.feed(data):
                    if ev.event == 'feed':
                        yield json.loads(ev.data)

            for ev in decoder.finish():
                if ev.event == 'feed':
                    yield json.loads(ev.data)

    async def stream_all(
            self,
            method: str,
            path: str,
            body: ta.Any = None,
    ) -> list[dict[str, ta.Any]]:
        return [e async for e in self.stream(method, path, body)]

    async def submit(self, text: str, *, after: int | None = None) -> list[dict[str, ta.Any]]:
        """Submits, and returns everything its stream carried through its end."""

        body: dict[str, ta.Any] = {'text': text}
        if after is not None:
            body['after'] = after

        return await self.stream_all('POST', '/api/submit', body)


@dc.dataclass()
class WebTestStreamError(Exception):
    status: int
    body: bytes


##


@dc.dataclass(frozen=True, kw_only=True)
class WebTestSession:
    web: RunningWeb
    client: WebTestClient


@contextlib.asynccontextmanager
async def web_test_session(
        backend: ta.Any,
        **config_kwargs: ta.Any,
) -> ta.AsyncIterator[WebTestSession]:
    config = WebConfig(
        port=0,
        in_memory=True,
        **config_kwargs,
    )

    async with running_web(
            config,
            overrides=[inj.bind(agn.BackendManager, to_const=agn.DictBackendManager.of(backend))],
    ) as rw:
        async with AsyncioIoPipelineAsyncHttpClient() as client:
            yield WebTestSession(
                web=rw,
                client=WebTestClient(client, rw.address.url, rw.token.v),
            )


def entry_types(entries: ta.Iterable[ta.Mapping[str, ta.Any]]) -> list[str]:
    return [e['type'] for e in entries]
