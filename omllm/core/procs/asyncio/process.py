"""
The asyncio `Process` handle. All state changes happen on the loop thread; the exit watcher thread only posts
callbacks. The `threading.Lock` guards the tiny signal/reap syscall critical sections so that a signal can never race
a reap even under a future free-threaded / multi-thread arrangement.

INVARIANTS:
- Signals are sent only while the process is unreaped and unpoisoned (SPAWNING/RUNNING/EXITED/ABANDONED) - in all
  of those the pid (and hence pgid) is still ours.
- `killpg` is only ever called with our own leader's pid.
- Reaping is the deliberate last step of `aclose()`, after the group sweep, under the lock.
"""
import asyncio
import os
import signal
import threading
import time
import typing as ta

from omcore import check
from omcore import lang
from omcore.logs import all as logs

from ..handles import Process
from ..spool.spool import OutputSpool
from ..types.errors import ProcessNotAliveError
from ..types.errors import ProcessPoisonedError
from ..types.errors import ProcessTimeoutError
from ..types.errors import StuckProcessError
from ..types.events import ProcessAbandonedEvent
from ..types.events import ProcessExitedEvent
from ..types.events import ProcessPoisonedEvent
from ..types.events import ProcessReapedEvent
from ..types.ids import ProcessId
from ..types.options import ProcOptions
from ..types.options import TerminationPolicy
from ..types.options import get_termination_policy
from ..types.specs import ProcessSpec
from ..types.states import ProcessState
from .pipes import StdinWriter
from .reaper import ExitWatcher
from .spawn import _SpawnerPopen


if ta.TYPE_CHECKING:
    from ..scopes.scope import ProcessScope
    from ..types.events import ProcessEvent


log = logs.get_module_logger(globals())


##


class ProcessOwner(ta.Protocol):
    """What a handle needs from its manager."""

    def _publish_soon(self, event: ProcessEvent) -> None: ...

    def _process_finished(self, process: AsyncioProcess) -> None: ...


##


class AsyncioProcess(Process):
    def __init__(
            self,
            *,
            id: ProcessId,  # noqa
            spec: ProcessSpec,
            options: ProcOptions,
            scope: ProcessScope,
            popen: _SpawnerPopen,
            spool: OutputSpool,
            stdin: StdinWriter | None,
            owner: ProcessOwner,
            loop: asyncio.AbstractEventLoop,
    ) -> None:
        super().__init__()

        self._id = id
        self._spec = spec
        self._options = options
        self._scope = scope
        self._popen = popen
        self._pid = check.isinstance(popen.pid, int)
        self._spool = spool
        self._stdin = stdin
        self._owner = owner
        self._loop = loop

        self._created_at = time.time()

        self._state = ProcessState.SPAWNING
        self._returncode: int | None = None
        self._lock = threading.Lock()

        self._exited_ev = asyncio.Event()
        self._output_ended_ev = asyncio.Event()
        self._reaped_ev = asyncio.Event()
        self._close_lock = asyncio.Lock()

        self._read_transports: dict[int, asyncio.ReadTransport] = {}
        self._open_output_fds: set[int] = set()

        self._watcher = ExitWatcher(
            self._pid,
            loop,
            on_exit=self._on_exit_observed,
            on_error=self._on_watcher_error,
        )

    def __repr__(self) -> str:
        return lang.attr_repr(self, 'id', 'pid', 'state', with_id=False)

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
    def options(self) -> ProcOptions:
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

    def _add_read_transport(self, fd: int, transport: asyncio.ReadTransport) -> None:
        self._read_transports[fd] = transport
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
            if self._state is ProcessState.SPAWNING:
                self._state = ProcessState.RUNNING

    #

    def _on_data(self, fd: int, data: bytes) -> None:
        if not self._spool.ended:
            self._spool.append(fd, data)

    def _on_output_eof(self, fd: int, exc: BaseException | None) -> None:
        self._open_output_fds.discard(fd)
        self._read_transports.pop(fd, None)
        if not self._open_output_fds and not self._output_ended_ev.is_set():
            self._spool.mark_ended()
            self._output_ended_ev.set()

    def _force_close_output(self) -> None:
        for t in list(self._read_transports.values()):
            try:
                t.close()
            except Exception:  # noqa
                log.exception('Error closing read transport of %r', self)
        # connection_lost callbacks arrive asynchronously; make the state consistent now.
        self._read_transports.clear()
        self._open_output_fds.clear()
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
        log.error('procs: process %r poisoned - it will never be signaled again: %s', self, reason)
        self._exited_ev.set()
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
                # group whose only remaining members are zombies. Because we only ever signal processes we still own,
                # a confirmed-dead target makes this benign; a still-live one is a genuine permission error to raise.
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
                rc = os.waitstatus_to_exitcode(status)
                if self._returncode is None:
                    self._returncode = rc
                # From here on the pid may be recycled by the OS.
                self._popen.returncode = rc
                self._state = ProcessState.REAPED
                reason = None
        self._reaped_ev.set()
        if reason is not None:
            log.error('procs: process %r poisoned: %s', self, reason)
            self._owner._publish_soon(ProcessPoisonedEvent(**self._event_kwargs(), reason=reason))  # noqa
        else:
            self._owner._publish_soon(ProcessReapedEvent(  # noqa
                **self._event_kwargs(),
                returncode=check.not_none(self._returncode),
            ))
        self._owner._process_finished(self)  # noqa

    def _abandon(self, reason: str) -> None:
        with self._lock:
            if self._state.is_terminal:
                return
            self._state = ProcessState.ABANDONED
        log.error('procs: abandoning process %r: %s', self, reason)
        self._force_close_output()
        self._owner._publish_soon(ProcessAbandonedEvent(**self._event_kwargs(), state=self._state))  # noqa
        self._owner._process_finished(self)  # noqa

    #

    @property
    def exited(self) -> bool:
        return self._exited_ev.is_set() and self._state is not ProcessState.POISONED

    async def wait(self, timeout: float | None = None) -> int:
        if not self._exited_ev.is_set():
            if timeout is None:
                await self._exited_ev.wait()
            else:
                try:
                    await asyncio.wait_for(self._exited_ev.wait(), timeout)
                except TimeoutError:
                    raise ProcessTimeoutError(f'{self!r} did not exit within {timeout}s') from None
        if self._state is ProcessState.POISONED:
            raise ProcessPoisonedError(repr(self))
        return check.not_none(self._returncode)

    async def _wait_exited(self, timeout: float) -> bool:
        if self._exited_ev.is_set():
            return True
        if timeout <= 0:
            return False
        try:
            await asyncio.wait_for(self._exited_ev.wait(), timeout)
        except TimeoutError:
            return False
        return True

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
    def spool(self) -> OutputSpool:
        return self._spool

    @property
    def output_ended(self) -> bool:
        return self._output_ended_ev.is_set()

    async def wait_output_ended(self, timeout: float | None = None) -> bool:
        if self._output_ended_ev.is_set():
            return True
        if timeout is None:
            await self._output_ended_ev.wait()
            return True
        if timeout <= 0:
            return False
        try:
            await asyncio.wait_for(self._output_ended_ev.wait(), timeout)
        except TimeoutError:
            return False
        return True

    #

    async def aclose(self, policy: TerminationPolicy | None = None) -> None:
        async with self._close_lock:
            if self._state.is_terminal:
                return

            pol = policy if policy is not None else self.termination_policy
            pg = pol.process_group

            # 1. Stop it if it is still alive.
            if not self._exited_ev.is_set():
                if pol.close_stdin and self._stdin is not None:
                    try:
                        await self._stdin.write_eof()
                    except Exception:  # noqa
                        pass

                self._signal_locked(pol.signal, pg)
                if not await self._wait_exited(pol.grace_s):
                    self._signal_locked(signal.SIGKILL, pg)
                    if not await self._wait_exited(pol.kill_s):
                        if self._state is ProcessState.POISONED:
                            return
                        reason = f'survived SIGKILL for {pol.kill_s}s'
                        if pol.on_stuck == 'raise':
                            self._abandon(reason)
                            raise StuckProcessError(f'{self!r} {reason}')
                        self._abandon(reason)
                        return

            if self._state is ProcessState.POISONED:
                return

            # 2. Sweep the group: anything the leader left behind (still holding our pipes or not) goes with it.
            if pg:
                self._signal_if_owned(pol.signal, True)
            if not self._output_ended_ev.is_set():
                await self.wait_output_ended(pol.drain_s)
            if pg:
                self._signal_if_owned(signal.SIGKILL, True)
            if self._stdin is not None:
                self._stdin.abort()
            self._force_close_output()

            # 3. Only now give the pid back to the OS.
            self._reap()
