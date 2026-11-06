"""
What becomes of a line the user submits: a slash command runs, anything else goes to the agent as a prompt. Either way
it runs as a submission - a task of its own, bracketed in the feed by its start and end events - so that it belongs to
no request: a browser going away mid-run leaves the run running, and only `cancel` stops it.

Submissions run one at a time, and one made while another runs is rejected on the spot rather than queued - with the one
exception of a command allowed to run while busy, a `/steer` say, which runs alongside.
"""
import asyncio
import contextvars
import functools
import itertools
import typing as ta

from omcore import dataclasses as dc
from omcore.logs import all as logs

from ... import agent as agn
from ..commands.base import ArgsCommandError
from ..commands.manager import CommandsManager
from ..commands.manager import ParseCommandError
from ..commands.manager import ParsedCommand
from .feed import events as fe
from .feed.feed import Feed
from .texts import WebTextRenderer


log = logs.get_module_logger(globals())


##


class SubmissionError(Exception):
    pass


class EmptySubmissionError(SubmissionError):
    pass


class SubmitterBusyError(SubmissionError):
    """Something which cannot run alongside the submission is running already."""


class SubmitterClosedError(SubmissionError):
    pass


@ta.final
@dc.dataclass(frozen=True, kw_only=True, eq=False)
class Submission:
    id: str
    kind: fe.SubmissionKind
    text: str

    # Whether it held the submitter for itself while it ran, as everything but a command allowed while busy does.
    exclusive: bool

    task: asyncio.Task[None] = dc.field(repr=False)

    async def join(self) -> None:
        """Waits for it to end, however it ends."""

        await asyncio.gather(self.task, return_exceptions=True)


class _Outcome(ta.NamedTuple):
    status: str
    error: str | None = None


class Submitter:
    def __init__(
            self,
            *,
            agent: agn.Agent,
            commands: CommandsManager,
            feed: Feed,
            renderer: WebTextRenderer,
    ) -> None:
        super().__init__()

        self._agent = agent
        self._commands = commands
        self._feed = feed
        self._renderer = renderer

        # Never waited on: whoever finds it held is turned away.
        self._lock = asyncio.Lock()

        # What submissions run in: the context the session was set up in, rather than whatever request started them -
        # the request's asgi scope, say, which has no business riding along with an agent run.
        self._context = contextvars.copy_context()

        self._ids = itertools.count(1)
        self._current: Submission | None = None
        self._all: set[Submission] = set()
        self._closing = False

        # The ids of the submissions whose ends are yet to be fed.
        self._unended: set[str] = set()

    @property
    def current(self) -> Submission | None:
        """The exclusive submission running, if one is."""

        return self._current

    @property
    def is_busy(self) -> bool:
        return self._lock.locked()

    #

    async def _run_prompt(self, text: str) -> _Outcome:
        result = await self._agent.prompt(text)

        return _Outcome(
            result.reason.name.lower(),
            repr(result.error) if result.error is not None else None,
        )

    async def _run_command(self, parsed: ParsedCommand) -> _Outcome:
        try:
            rc = await parsed.run()

        except ArgsCommandError as e:
            # Bad arguments are the user's to fix, so they get the usage rather than a traceback.
            lines = [str(e.arg_error)] if e.arg_error is not None else []
            lines.append(e.help)
            self._feed.append(fe.TextFeedEvent(text=self._renderer.render('\n'.join(lines))))
            return _Outcome('failure')

        return _Outcome(rc.value)

    async def _run_parse_error(self, e: ParseCommandError) -> _Outcome:
        if e.message is not None:
            self._feed.append(fe.TextFeedEvent(text=self._renderer.render(e.message)))

        return _Outcome('failure')

    async def _run(self, sub_id: str, fn: ta.Callable[[], ta.Awaitable[_Outcome]]) -> None:
        outcome = _Outcome('error')

        try:
            outcome = await fn()

        except asyncio.CancelledError:
            outcome = _Outcome('cancelled')
            raise

        except Exception as e:
            log.exception('Submission %s failed', sub_id)
            outcome = _Outcome('error', repr(e))
            self._feed.append(fe.NoticeFeedEvent(text=f'error: {e!r}', level='error'))

        finally:
            self._end(sub_id, outcome)

    def _end(self, sub_id: str, outcome: _Outcome) -> None:
        if sub_id not in self._unended:
            return
        self._unended.discard(sub_id)

        self._feed.append(fe.SubmissionEndFeedEvent(
            id=sub_id,
            status=outcome.status,
            error=outcome.error,
        ))

    def _on_done(self, sub: Submission) -> None:
        # A task cancelled before its first step never runs its body at all, so its end is fed here instead: without
        # one, every page would take it to be running forever.
        self._end(sub.id, _Outcome('cancelled'))

        self._all.discard(sub)

        if sub.exclusive:
            if self._current is sub:
                self._current = None
            self._lock.release()

    #

    async def submit(self, text: str) -> Submission:
        """
        Starts the submission and returns it, its start already in the feed. Raises SubmitterBusyError, having started
        nothing, if it cannot run now.
        """

        if self._closing:
            raise SubmitterClosedError

        if not (text := text.strip()):
            raise EmptySubmissionError

        kind: fe.SubmissionKind
        fn: ta.Callable[[], ta.Awaitable[_Outcome]]
        exclusive = True

        if text.startswith('/'):
            kind = 'command'

            try:
                parsed = self._commands.parse(text[1:])

            except ParseCommandError as e:
                # Runs nothing, so there is nothing for it to run alongside.
                fn = functools.partial(self._run_parse_error, e)
                exclusive = False

            else:
                fn = functools.partial(self._run_command, parsed)
                exclusive = not (parsed.command.can_run_while_busy and self._lock.locked())

        else:
            kind = 'prompt'
            fn = functools.partial(self._run_prompt, text)

        if exclusive:
            if self._lock.locked():
                raise SubmitterBusyError

            # Does not suspend - the lock was free just now, and no one ever waits on it - so nothing can slip in.
            await self._lock.acquire()

        try:
            return self._start(text, kind, fn, exclusive=exclusive)

        except BaseException:
            if exclusive:
                self._lock.release()
            raise

    def _start(
            self,
            text: str,
            kind: fe.SubmissionKind,
            fn: ta.Callable[[], ta.Awaitable[_Outcome]],
            *,
            exclusive: bool,
    ) -> Submission:
        sub_id = str(next(self._ids))
        self._unended.add(sub_id)

        self._feed.append(
            fe.SubmissionStartFeedEvent(
                id=sub_id,
                kind=kind,
                text=text,
                exclusive=exclusive,
            ),
            fe.UserMessageFeedEvent(text=text) if kind == 'prompt' else fe.CommandEchoFeedEvent(text=text),
        )

        sub = Submission(
            id=sub_id,
            kind=kind,
            text=text,
            exclusive=exclusive,
            task=asyncio.get_running_loop().create_task(
                self._run(sub_id, fn),
                context=self._context.copy(),
            ),
        )

        self._all.add(sub)
        if exclusive:
            self._current = sub

        sub.task.add_done_callback(lambda _: self._on_done(sub))

        return sub

    def cancel(self) -> bool:
        """Cancels the exclusive submission running, if there is one - a prompt's run, in the main."""

        if (sub := self._current) is None or sub.task.done():
            return False

        if not sub.task.cancelling():
            sub.task.cancel()

        return True

    async def aclose(self) -> None:
        self._closing = True

        subs = list(self._all)
        for sub in subs:
            if not sub.task.cancelling():
                sub.task.cancel()

        if subs:
            await asyncio.gather(*[sub.task for sub in subs], return_exceptions=True)
