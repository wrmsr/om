"""Small helpers for answering requests, and for reading what they carry."""
import typing as ta
import urllib.parse

from omcore.formats.json import all as json
from omcore.http import asgi


##


class BadWebRequestError(Exception):
    pass


async def send_bytes_response(
        send: asgi.Send,
        status: int,
        body: bytes,
        *,
        content_type: str,
        headers: ta.Sequence[tuple[bytes, bytes]] = (),
) -> None:
    await send({
        'type': 'http.response.start',
        'status': status,
        'headers': [
            (b'content-type', content_type.encode('latin-1')),
            (b'content-length', str(len(body)).encode('ascii')),
            (b'cache-control', b'no-cache'),
            (b'connection', b'close'),
            *headers,
        ],
    })

    await send({
        'type': 'http.response.body',
        'body': body,
    })


async def send_json_response(send: asgi.Send, status: int, obj: ta.Any) -> None:
    await send_bytes_response(
        send,
        status,
        json.dumps_compact(obj).encode('utf-8'),
        content_type='application/json; charset=utf-8',
    )


async def send_error_response(send: asgi.Send, status: int, error: str, message: str | None = None) -> None:
    await send_json_response(send, status, {
        'error': error,
        **({'message': message} if message is not None else {}),
    })


#


def query_int(scope: asgi.Scope, name: str, default: int = 0) -> int:
    qs = urllib.parse.parse_qs(scope['query_string'].decode('latin-1'))

    if not (vs := qs.get(name)):
        return default

    try:
        v = int(vs[-1])
    except ValueError:
        raise BadWebRequestError(f'{name} must be an integer') from None

    if v < 0:
        raise BadWebRequestError(f'{name} must not be negative')

    return v


async def read_json_body(recv: asgi.Recv) -> ta.Mapping[str, ta.Any]:
    body = await asgi.read_body(recv)

    if not body:
        return {}

    try:
        obj = json.loads(body.decode('utf-8'))
    except ValueError:
        raise BadWebRequestError('body must be json') from None

    if not isinstance(obj, dict):
        raise BadWebRequestError('body must be a json object')

    return obj
