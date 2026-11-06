import re
import typing as ta

from .... import lang
from ... import asgi
from ..base import BaseServerUrl
from ..routes import Route
from ..routes import RouteHandlerApp


##


async def _ok(scope: asgi.Scope, recv: asgi.Recv, send: asgi.Send) -> None:
    await asgi.send_response(send, 200, body=b'ok')


def _request(app: RouteHandlerApp, method: str, path: str) -> tuple[int, ta.Mapping[bytes, bytes]]:
    sent: list[asgi.Message] = []

    async def recv() -> asgi.Message:
        return {'type': 'http.request', 'body': b''}

    async def send(msg: asgi.Message) -> None:
        sent.append(msg)

    lang.sync_await(app(
        {
            'type': 'http',
            'method': method,
            'path': path,
            'raw_path': path.encode(),
        },
        recv,
        send,
    ))

    start = sent[0]
    return start['status'], dict(start['headers'])


def test_routing():
    app = RouteHandlerApp(
        {
            Route.get('/a'): _ok,
            Route.put('/a'): _ok,
            Route.post(re.compile(r'/b/\d+')): _ok,
        },
        BaseServerUrl('http://localhost/'),
    )

    assert _request(app, 'GET', '/a')[0] == 200
    assert _request(app, 'POST', '/b/12')[0] == 200

    # Routed, just not for the method.
    status, headers = _request(app, 'POST', '/a')
    assert status == 405
    assert headers[b'allow'] == b'GET, PUT'

    status, headers = _request(app, 'GET', '/b/12')
    assert status == 405
    assert headers[b'allow'] == b'POST'

    assert _request(app, 'GET', '/c')[0] == 404
    assert _request(app, 'GET', '/b/x')[0] == 404
