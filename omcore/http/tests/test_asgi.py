import typing as ta

from ... import lang
from .. import asgi


##


def _sent(fn: ta.Callable[[asgi.Send], ta.Awaitable[None]]) -> list[ta.Mapping[str, ta.Any]]:
    out: list[ta.Mapping[str, ta.Any]] = []

    async def send(msg: asgi.Message) -> None:
        out.append(msg)

    lang.sync_await(fn(send))
    return out


def test_send_response_says_how_long():
    start, body = _sent(lambda send: asgi.send_response(send, 200, body=b'hello'))

    assert (b'content-length', b'5') in start['headers']
    assert body['body'] == b'hello'


def test_send_response_keeps_a_given_length():
    start, _ = _sent(lambda send: asgi.send_response(
        send,
        200,
        headers=[(b'Content-Length', b'5')],
        body=b'hello',
    ))

    assert [k for k, _ in start['headers'] if k.lower() == b'content-length'] == [b'Content-Length']


def test_redirect_response_says_how_long():
    start, _ = _sent(lambda send: asgi.redirect_response(send, '/there'))

    assert (b'content-length', b'0') in start['headers']
    assert (b'location', b'/there') in start['headers']


def test_read_body():
    messages: list[asgi.Message] = [
        {'type': 'http.request', 'body': b'he', 'more_body': True},
        {'type': 'http.request', 'body': b'', 'more_body': True},
        {'type': 'http.request', 'body': b'llo'},
    ]

    async def recv() -> asgi.Message:
        return messages.pop(0)

    assert lang.sync_await(asgi.read_body(recv)) == b'hello'
    assert not messages
