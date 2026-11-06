"""
The web frontend's permission asker. `PermissionAsker.ask` is awaited from deep inside a tool executor, mid-run: here
the ask goes into the feed - beside the asking call's card, with the change it would make, if it says - and the
execution parks on a future until someone answers it, which they do out of band, through `answer`. Any number of asks
may be pending at once, each answered on its own.
"""
import asyncio
import itertools
import typing as ta

from omcore import check

from ... import agent as agn
from .feed import events as fe
from .feed.feed import Feed
from .texts import WebTextRenderer
from .tools import tool_card_key


##


class UnknownPermissionAskError(Exception):
    """No ask with the given id is waiting for an answer - it never was, or it already has one."""


class FeedPermissionAsker(agn.PermissionAsker):
    def __init__(
            self,
            *,
            feed: Feed,
            renderer: WebTextRenderer,
    ) -> None:
        super().__init__()

        self._feed = feed
        self._renderer = renderer

        self._seq = itertools.count(1)
        self._pending: dict[str, asyncio.Future[bool]] = {}

    @staticmethod
    def _describe_requestor(requestor: agn.PermissionRequestor) -> str:
        if (context := requestor.tool_context) is not None and (tool := context.tool) is not None:
            return tool.name
        return repr(requestor)

    def pending_ids(self) -> ta.AbstractSet[str]:
        return frozenset(self._pending)

    def answer(self, ask_id: str, allowed: bool) -> None:
        if (fut := self._pending.get(ask_id)) is None or fut.done():
            raise UnknownPermissionAskError(ask_id)

        fut.set_result(allowed)

    async def ask(
            self,
            request: agn.PermissionRequest,
            rule: agn.PermissionRule,
    ) -> agn.DecidedPermissionState:
        ask_id = str(next(self._seq))
        context = request.requestor.tool_context

        fut: asyncio.Future[bool] = asyncio.get_running_loop().create_future()
        self._pending[ask_id] = fut

        self._feed.append(fe.PermissionAskFeedEvent(
            id=ask_id,
            key=tool_card_key(context) if context is not None else None,
            tool=self._describe_requestor(request.requestor),
            target=repr(request.target),
            rule=repr(rule),
            preview=self._renderer.render(preview) if (preview := request.preview) is not None else None,
        ))

        outcome: fe.PermissionOutcome = 'aborted'
        try:
            allowed = await fut

        except asyncio.CancelledError:
            # The future is only ever cancelled with the task awaiting it - by the run's own cancellation, in practice -
            # but should anything else cancel it, that is the ask withdrawn rather than a cancellation of the run.
            if not check.not_none(asyncio.current_task()).cancelling():
                raise agn.PermissionAskAbortedError(request.target) from None
            raise

        else:
            outcome = 'allow' if allowed else 'deny'

        finally:
            del self._pending[ask_id]
            self._feed.append(fe.PermissionAnswerFeedEvent(id=ask_id, outcome=outcome))

        return agn.PermissionState.ALLOW if allowed else agn.PermissionState.DENY
