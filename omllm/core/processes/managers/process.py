"""
The implementation-agnostic `Process` handle: the state machine, the signal / reap discipline, the group teardown
algorithm, output-ended bookkeeping and the exit watcher wiring all live here. All state changes happen on the owner's
thread; the exit watcher thread only posts callbacks back (via the `_post_threadsafe` hook). Waiting is done through
`asynclite` events and locks handed in by the manager, so the only thing an implementation adds is how its runtime
schedules those callbacks and how it plumbs pipes (`ProcessStdinWriter`, output channel closers).

The `threading.Lock` guards the tiny signal/reap syscall critical sections so that a signal can never race a reap even
under a future free-threaded / multi-thread arrangement.

INVARIANTS:
- Signals are sent only while the process is unreaped and unpoisoned (SPAWNING/RUNNING/EXITED/ABANDONED) - the held pid
  is therefore still ours.
- `killpg` is only ever called with that held pid. Once a group exists with that id it can only be the child's group;
  before the shim's setsid fallback creates it, signaling it harmlessly reports ESRCH.
- Reaping is the deliberate last step of `aclose()`, after the group sweep, under the lock.
"""
import abc
import os
import signal
import threading
import time
import typing as ta

from omcore import check
from omcore import lang
from omcore.asyncs.asynclite import all as asl
from omcore.logs import all as logs

from ..handles import Process
from ..spool.spool import OutputSpool
from ..types.errors import NotAPtyError
from ..types.errors import ProcessNotAliveError
from ..types.errors import ProcessPoisonedError
from ..types.errors import ProcessTimeoutError
from ..types.errors import StuckProcessError
from ..types.events import ProcessAbandonedEvent
from ..types.events import ProcessExitedEvent
from ..types.events import ProcessPoisonedEvent
from ..types.events import ProcessReapedEvent
from ..types.ids import ProcessId
from ..types.options import ProcessOptions
from ..types.options import TerminationPolicy
from ..types.options import get_termination_policy
from ..types.specs import ProcessSpec
from ..types.states import ProcessState
from . import pty as _pty
from .reaper import ExitWatcher


if ta.TYPE_CHECKING:
    from ..scopes.scope import ProcessScope
    from ..types.events import ProcessEvent


log = logs.get_module_logger(globals())


##


class ProcessOwner(ta.Protocol):
    """What a handle needs from its manager."""

    def _publish_soon(self, event: ProcessEvent) -> None: ...

    def _process_finished(self, process: BaseProcess) -> None: ...

    def _spawn_task(self, coro: ta.Coroutine[ta.Any, ta.Any, ta.Any]) -> None: ...


class ProcessStdinWriter(lang.Abstract):
    """The implementation's write side of the child's stdin (a pipe or the pty master)."""

    @property
    @abc.abstractmethod
    def closed(self) -> bool:
        raise NotImplementedError

    @abc.abstractmethod
    def write(self, data: bytes) -> ta.Awaitable[None]:
        """Writes with backpressure. Raises BrokenPipeError if the child has closed its end."""

        raise NotImplementedError

    @abc.abstractmethod
    def write_eof(self) -> ta.Awaitable[None]:
        raise NotImplementedError

    @abc.abstractmethod
    def abort(self) -> None:
        """Drops any buffered data and closes immediately."""

        raise NotImplementedError


##


class BaseProcess(Process, lang.Abstract):
    def __init__(
            self,
            *,
            id: ProcessId,  # noqa
            spec: ProcessSpec,
            options: ProcessOptions,
            scope: ProcessScope,
            pid: int,
            spool: OutputSpool,
            pty_master_fd: int | None = None,
            process_group_ready: bool = True,
            owner: ProcessOwner,
            asynclite: asl.All,
    ) -> None:
        super().__init__()

        self._id = id
        self._spec = spec
        self._options = options
        self._scope = scope
        self._pid = check.isinstance(pid, int)
        self._spool = spool
        self._pty_master_fd = pty_master_fd
        self._is_pty = pty_master_fd is not None
        self._process_group_ready = process_group_ready
        self._owner = owner
        self._asynclite = asynclite

        self._created_at = time.time()

        self._state = ProcessState.SPAWNING
        self._returncode: int | None = None
        self._lock = threading.Lock()

        self._exited_ev = asynclite.make_event()
        self._output_ended_ev = asynclite.make_event()
        self._reaped_ev = asynclite.make_event()

        # The teardown in flight, if any: set while its manager task runs, and what waiters wait on.
        self._close_attempt: asl.Event | None = None
        self._close_error: BaseException | None = None

        self._stdin: ProcessStdinWriter | None = None

        # Output channels by spool fd number: each maps to a closer that force-closes the implementation's reader.
        self._output_closers: dict[int, ta.Callable[[], None]] = {}
        self._open_output_fds: set[int] = set()

        self._watcher = ExitWatcher(
            self._pid,
            post=self._post_threadsafe,
            on_exit=self._on_exit_observed,
            on_error=self._on_watcher_error,
        )

    def __repr__(self) -> str:
        return lang.attr_repr(self, 'id', 'pid', 'state', with_id=False)

    #

    @abc.abstractmethod
    def _post_threadsafe(self, fn: ta.Callable, *args: ta.Any) -> None:
        """
        Schedules `fn(*args)` on the owner's thread from any thread (the exit watcher's). Raises RuntimeError if the
        owner is gone.
        """

        raise NotImplementedError

    #

    @property
    def id(self) -> ProcessId:
        return self._id

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def spec(self) -> ProcessSpec:
        return self._spec

    @property
    def options(self) -> ProcessOptions:
        return self._options

    @property
    def state(self) -> ProcessState:
        return self._state

    @property
    def returncode(self) -> int | None:
        return self._returncode

    @property
    def scope(self) -> ProcessScope:
        return self._scope

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def termination_policy(self) -> TerminationPolicy:
        return get_termination_policy(self._options)

    #

    def _set_scope(self, scope: ProcessScope) -> None:
        self._scope = scope

    def _set_stdin(self, stdin: ProcessStdinWriter) -> None:
        check.none(self._stdin)
        if self._state.is_terminal:
            # Torn down while the pipe was still connecting: don't hold a channel nobody will ever close.
            stdin.abort()
            return
        self._stdin = stdin

    def _add_output_channel(self, fd: int, close: ta.Callable[[], None]) -> None:
        """
        Registers a connected output reader for spool fd `fd`; `close` force-closes it (see `_force_close_output`).
        """

        if self._state.is_terminal:
            # Torn down while the pipe was still connecting - `_force_close_output` has already run and will not again.
            close()
            return
        self._output_closers[fd] = close
        self._open_output_fds.add(fd)

    def _no_output(self) -> None:
        """No readable pipes at all - output is trivially ended."""

        if not self._open_output_fds:
            self._spool.mark_ended()
            self._output_ended_ev.set()

    def _start_watcher(self) -> None:
        self._watcher.start()

    def _mark_running(self) -> None:
        with self._lock:
            # A successful exec-status handshake proves the shim completed its setsid fallback before target exec.
            self._process_group_ready = True
            if self._state is ProcessState.SPAWNING:
                self._state = ProcessState.RUNNING

    #

    def _on_data(self, fd: int, data: bytes) -> None:
        if not self._spool.ended:
            self._spool.append(fd, data)

    def _on_output_eof(self, fd: int, exc: BaseException | None) -> None:
        self._open_output_fds.discard(fd)
        self._output_closers.pop(fd, None)
        if not self._open_output_fds and not self._output_ended_ev.is_set():
            self._spool.mark_ended()
            self._output_ended_ev.set()

    def _force_close_output(self) -> None:
        for close in list(self._output_closers.values()):
            try:
                close()
            except Exception:  # noqa
                log.exception('Error closing output channel of %r', self)
        # Implementations may report the close asynchronously; make the state consistent now.
        self._output_closers.clear()
        self._open_output_fds.clear()
        if (mfd := self._pty_master_fd) is not None:
            self._pty_master_fd = None
            try:
                os.close(mfd)
            except OSError:
                pass
        if not self._output_ended_ev.is_set():
            self._spool.mark_ended()
            self._output_ended_ev.set()

    def _event_kwargs(self) -> dict[str, ta.Any]:
        return dict(
            process_id=self._id,
            pid=self._pid,
            scope_path=tuple(self._scope.path),
        )

    def _on_exit_observed(self, returncode: int) -> None:
        with self._lock:
            if self._state not in (ProcessState.SPAWNING, ProcessState.RUNNING, ProcessState.ABANDONED):
                return
            was_abandoned = self._state is ProcessState.ABANDONED
            self._state = ProcessState.EXITED
            self._returncode = returncode
        self._exited_ev.set()
        self._owner._publish_soon(ProcessExitedEvent(**self._event_kwargs(), returncode=returncode))  # noqa
        if was_abandoned:
            # Nobody is coming back for it - finish it off now.
            self._force_close_output()
            self._reap()

    def _on_watcher_error(self, exc: BaseException) -> None:
        self._poison(f'exit watcher failed: {exc!r}')

    def _poison(self, reason: str) -> None:
        with self._lock:
            if self._state.is_terminal:
                return
            self._state = ProcessState.POISONED
        log.error('processes: process %r poisoned - it will never be signaled again: %s', self, reason)
        self._exited_ev.set()
        if (w := self._stdin) is not None:
            w.abort()
        self._force_close_output()
        self._owner._publish_soon(ProcessPoisonedEvent(**self._event_kwargs(), reason=reason))  # noqa
        self._owner._process_finished(self)  # noqa

    #

    def _signal_locked(self, sig: int, process_group: bool) -> None:
        with self._lock:
            if self._state in (ProcessState.REAPED, ProcessState.POISONED):
                raise ProcessNotAliveError(f'{self!r} is {self._state.name}')
            pid = self._pid
            check.arg(pid > 1)
            try:
                if process_group:
                    os.killpg(pid, sig)
                else:
                    os.kill(pid, sig)
            except ProcessLookupError:
                # ESRCH: the target is already gone. Benign - and never a recycled pid, since we hold the zombie
                # unreaped until teardown.
                pass
            except PermissionError:
                # macOS/BSD return EPERM (where Linux returns ESRCH / success) when signaling a zombie, or a process
                # group whose only remaining members are zombies. Because we only ever signal processes we still own, a
                # confirmed-dead target makes this benign; a still-live one is a genuine permission error to raise.
                if not self._is_exited_nowait(pid):
                    raise

    @staticmethod
    def _is_exited_nowait(pid: int) -> bool:
        """Non-reaping liveness probe: True iff the pid has exited (a zombie we still hold) or is already gone."""

        try:
            res = os.waitid(os.P_PID, pid, os.WEXITED | os.WNOHANG | os.WNOWAIT)
        except ChildProcessError:
            return True
        except OSError:
            return False
        return res is not None

    def _signal_if_owned(self, sig: int, process_group: bool) -> bool:
        try:
            self._signal_locked(sig, process_group)
        except ProcessNotAliveError:
            return False
        return True

    def _signal_for_termination(self, sig: int, process_group: bool) -> None:
        if process_group and not self._process_group_ready:
            # The shim may be either side of setsid. Signal the owned pid so it cannot escape before creating the
            # group, then sweep pgid==pid in case the session already exists (and may contain target descendants).
            self._signal_if_owned(sig, False)
            self._signal_if_owned(sig, True)
        else:
            self._signal_if_owned(sig, process_group)

    def _reap(self) -> None:
        with self._lock:
            if self._state in (ProcessState.REAPED, ProcessState.POISONED):
                return
            check.state(self._state is ProcessState.EXITED, f'cannot reap {self._state.name}')
            try:
                _, status = os.waitpid(self._pid, 0)
            except ChildProcessError as e:
                self._state = ProcessState.POISONED
                reason: str | None = f'reap failed: {e!r}'
            else:
                if self._returncode is None:
                    self._returncode = os.waitstatus_to_exitcode(status)
                # From here on the pid may be recycled by the OS.
                self._state = ProcessState.REAPED
                reason = None
        self._reaped_ev.set()
        if reason is not None:
            log.error('processes: process %r poisoned: %s', self, reason)
            self._owner._publish_soon(ProcessPoisonedEvent(**self._event_kwargs(), reason=reason))  # noqa
        else:
            self._owner._publish_soon(ProcessReapedEvent(  # noqa
                **self._event_kwargs(),
                returncode=check.not_none(self._returncode),
            ))
        self._owner._process_finished(self)  # noqa

    def _abandon(self, reason: str, *, kill: bool = False) -> None:
        """
        Gives up on a handle we are out of time for: it is unregistered, and its still-running exit watcher reaps it if
        it ever does exit. With `kill` the group is SIGKILLed first (the scope-close backstop: out of time, not out of
        options). A handle whose exit has already been *observed* has nothing to abandon - its watcher will never fire
        again, so leaving it would hold the zombie forever - it is swept and reaped right here instead.
        """

        with self._lock:
            if self._state.is_terminal:
                return
            exited = self._state is ProcessState.EXITED
            if not exited:
                self._state = ProcessState.ABANDONED

        if kill:
            try:
                self._signal_for_termination(signal.SIGKILL, self.termination_policy.process_group)
            except OSError:
                log.exception('processes: error killing %r at abandonment', self)
        if (w := self._stdin) is not None:
            w.abort()

        if exited:
            log.warning('processes: process %r had already exited at abandonment (%s) - reaping', self, reason)
            self._force_close_output()
            self._reap()
            return

        log.error('processes: abandoning process %r: %s', self, reason)
        self._force_close_output()
        self._owner._publish_soon(ProcessAbandonedEvent(**self._event_kwargs(), state=self._state))  # noqa
        self._owner._process_finished(self)  # noqa

    #

    @property
    def exited(self) -> bool:
        return self._exited_ev.is_set() and self._state is not ProcessState.POISONED

    async def _wait_exited(self, timeout: float | None) -> bool:
        if self._exited_ev.is_set():
            return True
        if timeout is not None and timeout <= 0:
            return False
        try:
            await self._exited_ev.wait(timeout=timeout)
        except TimeoutError:
            # The exit may have landed during the timeout's own cancellation handoff - the event is the truth.
            return self._exited_ev.is_set()
        return True

    async def wait(self, timeout: float | None = None) -> int:
        if not await self._wait_exited(timeout):
            raise ProcessTimeoutError(f'{self!r} did not exit within {timeout}s')
        if self._state is ProcessState.POISONED:
            raise ProcessPoisonedError(repr(self))
        return check.not_none(self._returncode)

    #

    async def signal(self, sig: int, *, process_group: bool | None = None) -> None:
        if process_group is None:
            process_group = self.termination_policy.process_group
        self._signal_locked(sig, process_group)

    async def terminate(self) -> None:
        await self.signal(self.termination_policy.signal)

    async def kill(self) -> None:
        await self.signal(signal.SIGKILL)

    #

    @property
    def has_stdin(self) -> bool:
        return self._stdin is not None

    @property
    def stdin_closed(self) -> bool:
        return self._stdin is None or self._stdin.closed

    async def write(self, data: bytes) -> None:
        if (w := self._stdin) is None:
            raise BrokenPipeError('process has no stdin pipe')
        await w.write(data)

    async def write_eof(self) -> None:
        if (w := self._stdin) is not None:
            await w.write_eof()

    #

    @property
    def has_pty(self) -> bool:
        return self._is_pty

    async def resize(self, rows: int, cols: int) -> None:
        if not self._is_pty:
            raise NotAPtyError(repr(self))
        if (mfd := self._pty_master_fd) is None:
            raise ProcessNotAliveError(f'{self!r} pty is torn down')
        _pty.set_winsize(mfd, rows, cols)

    def get_winsize(self) -> tuple[int, int] | None:
        if (mfd := self._pty_master_fd) is None:
            return None
        try:
            ws = _pty.get_winsize(mfd)
        except OSError:
            return None
        return (ws.rows, ws.cols)

    #

    @property
    def spool(self) -> OutputSpool:
        return self._spool

    @property
    def output_ended(self) -> bool:
        return self._output_ended_ev.is_set()

    async def wait_output_ended(self, timeout: float | None = None) -> bool:
        if self._output_ended_ev.is_set():
            return True
        if timeout is not None and timeout <= 0:
            return False
        try:
            await self._output_ended_ev.wait(timeout=timeout)
        except TimeoutError:
            return self._output_ended_ev.is_set()
        return True

    #

    @property
    def closing(self) -> bool:
        return self._close_attempt is not None

    async def aclose(
            self,
            policy: TerminationPolicy | None = None,
            *,
            wait_s: float | None = None,
    ) -> None:
        if self._state.is_terminal:
            return

        if (ev := self._close_attempt) is None:
            # The teardown is the manager's task, not the caller's. The usual reason to be closing a live process is
            # that the caller is being cancelled, and a cancellation must not take the teardown down with it: whether
            # the caller waits for it or not, it runs to its end under the manager, which joins it before it closes.
            ev = self._close_attempt = self._asynclite.make_event()
            self._owner._spawn_task(self._run_close(  # noqa
                policy if policy is not None else self.termination_policy,
                ev,
            ))

        if wait_s is None:
            await ev.wait()
        else:
            try:
                await ev.wait(timeout=wait_s)
            except TimeoutError:
                return

        if (e := self._close_error) is not None:
            # Raised once, to the first waiter to see it: a later aclose is the idempotent no-op it always was.
            self._close_error = None
            raise e

    async def _run_close(self, pol: TerminationPolicy, ev: asl.Event) -> None:
        try:
            await self._close(pol)

        except StuckProcessError as e:
            # Already logged and published by the abandonment; kept for a waiter.
            self._close_error = e

        except BaseException as e:  # noqa
            log.exception('processes: error closing %r', self)
            self._close_error = e

        finally:
            self._close_attempt = None
            ev.set()

    def _overtaken(self) -> bool:
        """
        Whether the teardown has been overtaken while it waited - a scope's close backstop abandoning the process, a
        poisoning - leaving it nothing more to do.
        """

        return self._state.is_terminal

    async def _close(self, pol: TerminationPolicy) -> None:
        """The teardown itself. Every wait in it is followed by a look at whether it has been overtaken."""

        pg = pol.process_group

        # 1. Stop it if it is still alive.
        if not self._exited_ev.is_set():
            if pol.close_stdin and self._stdin is not None:
                try:
                    await self._stdin.write_eof()
                except Exception:  # noqa
                    pass

            self._signal_for_termination(pol.signal, pg)
            if not await self._wait_exited(pol.grace_s):
                if self._overtaken():
                    return
                self._signal_for_termination(signal.SIGKILL, pg)
                if not await self._wait_exited(pol.kill_s):
                    if self._overtaken():
                        return
                    reason = f'survived SIGKILL for {pol.kill_s}s'
                    if pol.on_stuck == 'raise':
                        self._abandon(reason)
                        raise StuckProcessError(f'{self!r} {reason}')
                    self._abandon(reason)
                    return

        if self._overtaken():
            return

        # 2. Sweep the group: anything the leader left behind (still holding our pipes or not) goes with it.
        if pg:
            self._signal_if_owned(pol.signal, True)
        if not self._output_ended_ev.is_set():
            await self.wait_output_ended(pol.drain_s)
            if self._overtaken():
                return
        if pg:
            self._signal_if_owned(signal.SIGKILL, True)
        if self._stdin is not None:
            self._stdin.abort()
        self._force_close_output()

        # 3. Only now give the pid back to the OS.
        self._reap()
