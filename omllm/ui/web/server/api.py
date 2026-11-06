"""
The api, all of it json in and json or sse out:

  - `GET /api/info` - the session, as `WebInfo`.
  - `GET /api/feed?after=<seq>` - the feed's entries after a cursor.
  - `GET /api/feed/stream?after=<seq>` - the same, then everything after as it comes, as sse, for as long as the
    connection stays open.
  - `POST /api/submit` `{"text": ..., "after": <seq>}` - starts a submission, and streams the feed as sse from the
    cursor through the submission's end. 409 if something which cannot run alongside it is running.
  - `POST /api/cancel` - cancels the running submission, if there is one.
  - `POST /api/permissions` `{"id": ..., "allow": <bool>}` - answers a pending permission ask.
"""
from omcore import marshal as msh
from omcore.http import asgi
from omcore.http.apps.routes import Route
from omcore.http.apps.routes import RouteHandlerHolder
from omcore.http.apps.routes import handles

from ..feed.events import ShutdownFeedEvent
from ..feed.events import SubmissionEndFeedEvent
from ..feed.feed import Feed
from ..feed.feed import FeedEntry
from ..info import WebInfo
from ..info import WebInfoBuilder
from ..permissions import FeedPermissionAsker
from ..permissions import UnknownPermissionAskError
from ..quit import WebQuitSignal
from ..submissions import EmptySubmissionError
from ..submissions import Submitter
from ..submissions import SubmitterBusyError
from ..submissions import SubmitterClosedError
from .responses import BadWebRequestError
from .responses import query_int
from .responses import read_json_body
from .responses import send_error_response
from .responses import send_json_response
from .sse import FeedSseStreamer
from .sse import marshal_feed_entry


##


class WebApiHandlers(RouteHandlerHolder):
    def __init__(
            self,
            *,
            feed: Feed,
            submitter: Submitter,
            permission_asker: FeedPermissionAsker,
            info_builder: WebInfoBuilder,
            streamer: FeedSseStreamer,
            quit_signal: WebQuitSignal,
    ) -> None:
        super().__init__()

        self._quit_signal = quit_signal

        self._feed = feed
        self._submitter = submitter
        self._permission_asker = permission_asker
        self._info_builder = info_builder
        self._streamer = streamer

    @staticmethod
    def _is_shutdown(entry: FeedEntry) -> bool:
        return isinstance(entry.event, ShutdownFeedEvent)

    def _cursor(self, after: int) -> int:
        # A cursor past the end - from a page of an earlier server, say - would never see anything it waits for.
        return min(after, self._feed.last_seq)

    @handles(Route.get('/api/info'))
    async def handle_get_info(self, scope: asgi.Scope, recv: asgi.Recv, send: asgi.Send) -> None:
        await send_json_response(send, 200, msh.marshal(self._info_builder.build_info(), WebInfo))

    @handles(Route.get('/api/feed'))
    async def handle_get_feed(self, scope: asgi.Scope, recv: asgi.Recv, send: asgi.Send) -> None:
        after = self._cursor(query_int(scope, 'after'))

        await send_json_response(send, 200, {
            'entries': [marshal_feed_entry(e) for e in self._feed.entries_after(after)],
            'last_seq': self._feed.last_seq,
        })

    @handles(Route.get('/api/feed/stream'))
    async def handle_get_feed_stream(self, scope: asgi.Scope, recv: asgi.Recv, send: asgi.Send) -> None:
        after = self._cursor(query_int(scope, 'after'))

        # Ends with the session, rather than being cut off as the server stops.
        await self._streamer.start_response(send)
        await self._streamer.stream(send, after=after, until=self._is_shutdown)
        await self._streamer.finish_response(send)

    @handles(Route.post('/api/submit'))
    async def handle_post_submit(self, scope: asgi.Scope, recv: asgi.Recv, send: asgi.Send) -> None:
        body = await read_json_body(recv)

        if not isinstance(text := body.get('text'), str):
            raise BadWebRequestError('text must be a string')

        if not isinstance(after := body.get('after', self._feed.last_seq), int) or after < 0:
            raise BadWebRequestError('after must be a non-negative integer')
        after = self._cursor(after)

        try:
            sub = await self._submitter.submit(text)

        except EmptySubmissionError:
            raise BadWebRequestError('text must not be empty') from None

        except SubmitterBusyError:
            await send_error_response(send, 409, 'busy', 'Something is already running.')
            return

        except SubmitterClosedError:
            await send_error_response(send, 503, 'closed', 'The session is shutting down.')
            return

        def is_end(entry: FeedEntry) -> bool:
            if self._is_shutdown(entry):
                return True

            # Ending as the session is quitting, it goes on through the announcement of its end.
            return (
                isinstance(ev := entry.event, SubmissionEndFeedEvent) and
                ev.id == sub.id and
                not self._quit_signal.is_set
            )

        await self._streamer.start_response(send)
        await self._streamer.stream(send, after=after, until=is_end)
        await self._streamer.finish_response(send)

    @handles(Route.post('/api/cancel'))
    async def handle_post_cancel(self, scope: asgi.Scope, recv: asgi.Recv, send: asgi.Send) -> None:
        await read_json_body(recv)

        await send_json_response(send, 200, {'cancelled': self._submitter.cancel()})

    @handles(Route.post('/api/permissions'))
    async def handle_post_permissions(self, scope: asgi.Scope, recv: asgi.Recv, send: asgi.Send) -> None:
        body = await read_json_body(recv)

        if not isinstance(ask_id := body.get('id'), str):
            raise BadWebRequestError('id must be a string')

        if not isinstance(allow := body.get('allow'), bool):
            raise BadWebRequestError('allow must be a boolean')

        try:
            self._permission_asker.answer(ask_id, allow)
        except UnknownPermissionAskError:
            await send_error_response(send, 404, 'unknown_ask', 'No such permission ask is pending.')
            return

        await send_json_response(send, 200, {})
