# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
The runtime seam: the one place the sync and asyncio connections differ.

A connection is written once, async-colored, against this interface. Everything whose mechanics depend on how the
process waits and runs things is behind it: making a promise and waiting on it, starting the pump which steps the
pipeline driver and feeds its events back, running a handler, and cancelling one.

The sync runtime holds a sync-stepped driver. Waiting on one of its promises pumps the driver in the caller's thread
until the promise is done, and never actually suspends, so `sync_await` drives the whole stack. Handlers run inline,
one at a time, as the events which caused them are delivered. The asyncio runtime holds an asyncio driver, runs one
pump task, backs promises with futures, and runs handlers as tracked tasks. A future runtime for another loop - or a
callback-only one for a reactor which cannot wait - is a third implementation of this interface and nothing else.
"""
import abc
import typing as ta

from ..asyncs.asynclite.promises import AsynclitePromise
from ..lite.abstract import Abstract


##


class RpcRuntimeSink(Abstract):
    """What a runtime feeds: the connection."""

    @abc.abstractmethod
    async def on_event(self, event: ta.Any) -> None:
        """
        An unhandled output of the pipeline driver, which for an rpc pipeline is a session event. Awaited on the pump,
        so inline work here holds up everything behind it in wire order.

        A raw exception output - which the session surfaces on a failing close, so it reaches the host even past a
        stalled transport flush - is not delivered here: the runtime takes it as the driver's failure, aborts the
        driver, and reports it through `on_driver_done`.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def on_driver_done(self, exc: ta.Optional[BaseException]) -> None:
        """
        The driver stopped running, cleanly or with the given failure. Called exactly once per started runtime: by the
        pump when the driver stops, or by `close` when the runtime is closed before that.
        """

        raise NotImplementedError


class RpcRuntime(Abstract):
    @property
    @abc.abstractmethod
    def is_started(self) -> bool:
        raise NotImplementedError

    @property
    @abc.abstractmethod
    def is_driver_done(self) -> bool:
        """Whether the driver has stopped running; nothing enqueued after this will be processed."""

        raise NotImplementedError

    @abc.abstractmethod
    async def start(self, sink: RpcRuntimeSink) -> None:
        """Binds the sink and, where pumping is a background activity, starts it."""

        raise NotImplementedError

    #

    @abc.abstractmethod
    def make_promise(self) -> AsynclitePromise:
        """
        A promise whose `wait` behaves as the runtime does: by pumping the driver until it is done under a sync runtime,
        by suspending under an asyncio one. A wait timeout raises `AsynclitePromiseWaitTimeoutError`.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def is_cancelled_exception(self, exc: BaseException) -> bool:
        """Whether an exception raised out of a handler means the handler's task was cancelled, not that it failed."""

        raise NotImplementedError

    #

    @abc.abstractmethod
    def enqueue(self, *commands: ta.Any) -> bool:
        """Hands commands to the driver, returning False if it is no longer accepting them."""

        raise NotImplementedError

    @abc.abstractmethod
    async def spawn(self, key: ta.Any, fn: ta.Callable[[], ta.Awaitable[None]]) -> None:
        """
        Runs `fn` as a handler: inline, to completion, under a sync runtime; as a tracked task under asyncio, where
        `key` (if not None) identifies it to `cancel`. A handler's exceptions are its own business - `fn` is expected to
        report them to the peer itself - but a runtime observes and logs whatever escapes.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def cancel(self, key: ta.Any) -> None:
        """Cancels the handler spawned under `key`, if any and if still running. A no-op under a sync runtime."""

        raise NotImplementedError

    @abc.abstractmethod
    def cancel_all(self) -> None:
        raise NotImplementedError

    #

    @abc.abstractmethod
    async def close(self) -> None:
        """Aborts the driver and cancels every spawned handler. Idempotent."""

        raise NotImplementedError

    @abc.abstractmethod
    async def wait_closed(self) -> None:
        """Waits until the pump and every spawned handler have finished. Only meaningful once the driver is done."""

        raise NotImplementedError
