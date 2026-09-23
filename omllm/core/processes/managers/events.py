"""
Ordered delivery of a manager's `ProcessEvent`s. Events are queued as they are raised - from sync callbacks (an exit
watcher, a reparent, a remote notification) and async paths alike - and published one at a time by a single drain task,
so subscribers see them strictly in the order they happened even when they themselves suspend. The manager supplies how
to publish, how to run the drain task, and its async primitives.
"""
import collections
import contextvars
import typing as ta

from omcore.asyncs.asynclite import all as asl
from omcore.logs import all as logs

from ..types.events import ProcessEvent


log = logs.get_module_logger(globals())


##


# The drain the current task is publishing from, so a subscriber that publishes from within its own callback does not
# wait on the very drain it is running in.
_IN_DRAIN: contextvars.ContextVar[ProcessEventDrain | None] = contextvars.ContextVar(
    'om_processes_in_drain',
    default=None,
)


class ProcessEventDrain:
    def __init__(
            self,
            *,
            publish: ta.Callable[[ProcessEvent], ta.Awaitable[None]],
            spawn_task: ta.Callable[[ta.Coroutine[ta.Any, ta.Any, ta.Any]], None],
            asynclite: asl.All,
    ) -> None:
        super().__init__()

        self._publish = publish
        self._spawn_task = spawn_task
        self._asynclite = asynclite

        self._queue: collections.deque[ProcessEvent] = collections.deque()
        self._enabled = False
        self._draining = False
        self._idle = asynclite.make_event()
        self._idle.set()

    @property
    def busy(self) -> bool:
        """Whether anything is queued or being delivered."""

        return bool(self._queue) or self._draining

    def enable(self) -> None:
        """Starts delivering. Events queued before this are kept, and go out first."""

        self._enabled = True
        self.ensure_draining()

    async def _drain(self) -> None:
        tok = _IN_DRAIN.set(self)
        try:
            while self._queue:
                e = self._queue.popleft()
                try:
                    await self._publish(e)
                except Exception:  # noqa
                    log.exception('processes: error publishing event %r', e)
        finally:
            _IN_DRAIN.reset(tok)
            self._draining = False
            self._idle.set()
            if self._queue:
                # Raced with a late enqueue.
                self.ensure_draining()

    def ensure_draining(self) -> None:
        if self._draining or not self._enabled or not self._queue:
            return
        self._draining = True
        # A fresh idle event per drain: everyone waiting on the previous one has been released.
        self._idle = self._asynclite.make_event()
        self._spawn_task(self._drain())

    def publish_soon(self, event: ProcessEvent) -> None:
        self._queue.append(event)
        self.ensure_draining()

    async def publish_now(self, event: ProcessEvent) -> None:
        """Enqueues in order and waits until it (and everything before it) has been delivered."""

        self.publish_soon(event)
        if not self._enabled or _IN_DRAIN.get() is self:
            # Not delivering yet, or published from within a subscriber: the running drain will get to it - waiting
            # would deadlock.
            return
        while self.busy:
            if not self._draining:
                self.ensure_draining()
                continue
            await self._idle.wait()
