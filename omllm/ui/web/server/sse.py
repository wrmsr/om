"""
The feed, streamed as server-sent events. Each feed entry goes out as one `feed` event - its seq as the event's id, and
as its data the marshaled feed event with the seq merged in:

    id: 12
    event: feed
    data: {"seq":12,"type":"ai_text_delta","text":"Hel"}

A stream idle for a while sends a comment, so that a dead peer is found out and an idle connection is not reaped.
"""
import asyncio
import typing as ta

from omcore import check
from omcore import marshal as msh
from omcore.formats.json import all as json
from omcore.http import asgi

from ..feed.events import FeedEvent
from ..feed.feed import Feed
from ..feed.feed import FeedEntry


##


SSE_RESPONSE_HEADERS: ta.Sequence[tuple[bytes, bytes]] = [
    (b'content-type', b'text/event-stream; charset=utf-8'),
    (b'cache-control', b'no-cache'),
    (b'transfer-encoding', b'chunked'),
    (b'connection', b'close'),
]


def encode_sse_event(
        data: str,
        *,
        event: str | None = None,
        id: str | None = None,  # noqa
) -> bytes:
    lines: list[str] = []

    if id is not None:
        lines.append(f'id: {id}')

    if event is not None:
        lines.append(f'event: {event}')

    lines.extend(f'data: {l}' for l in data.split('\n'))

    return ('\n'.join(lines) + '\n\n').encode()


def encode_sse_comment(text: str = '') -> bytes:
    return f': {text}\n\n'.encode()


##


def marshal_feed_entry(entry: FeedEntry) -> dict[str, ta.Any]:
    return {
        'seq': entry.seq,
        **check.isinstance(msh.marshal(entry.event, FeedEvent), dict),
    }


def encode_feed_entry_sse(entry: FeedEntry) -> bytes:
    return encode_sse_event(
        json.dumps_compact(marshal_feed_entry(entry)),
        event='feed',
        id=str(entry.seq),
    )


##


class FeedSseStreamer:
    """
    Streams the feed from a cursor until told to stop. Waits with `asyncio.wait` rather than anything which cancels
    the current task, as the asgi app it runs in may not be a task of its own - the pipeline server steps it inside its
    connection's driver.
    """

    def __init__(
            self,
            *,
            feed: Feed,
            keepalive_s: float = 15.,
    ) -> None:
        super().__init__()

        self._feed = feed
        self._keepalive_s = keepalive_s

    async def start_response(self, send: asgi.Send) -> None:
        await send({
            'type': 'http.response.start',
            'status': 200,
            'headers': list(SSE_RESPONSE_HEADERS),
        })

    async def finish_response(self, send: asgi.Send) -> None:
        await send({
            'type': 'http.response.body',
            'body': b'',
            'more_body': False,
        })

    async def stream(
            self,
            send: asgi.Send,
            *,
            after: int,
            until: ta.Callable[[FeedEntry], bool] | None = None,
    ) -> None:
        """Sends every entry after the cursor as it comes, up to and including the first `until` is true of."""

        cursor = after

        while True:
            if entries := self._feed.entries_after(cursor):
                out: list[bytes] = []
                done = False

                for entry in entries:
                    out.append(encode_feed_entry_sse(entry))
                    cursor = entry.seq

                    if until is not None and until(entry):
                        done = True
                        break

                await send({
                    'type': 'http.response.body',
                    'body': b''.join(out),
                    'more_body': True,
                })

                if done:
                    return

                continue

            changed = self._feed.changed()
            await asyncio.wait([changed], timeout=self._keepalive_s)

            if not changed.done():
                await send({
                    'type': 'http.response.body',
                    'body': encode_sse_comment('keepalive'),
                    'more_body': True,
                })
