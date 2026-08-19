"""
The asyncio `ProcessManager`. See `_devdocs/design.md`. Everything asyncio-specific in procs lives in this package; the
abstract interfaces one level up are what the rest of the codebase depends on.
"""
import asyncio
import collections
import errno
import functools
import marshal
import os
import shutil
import signal
import subprocess
import tempfile
import types
import typing as ta
import weakref

from omcore import check
from omcore import lang
from omcore.logs import all as logs

from ..handles import Process
from ..launch.launcher import Launcher
from ..launch.shim import ShimLauncher
from ..manager import ManagerConfig
from ..manager import ProcessManager
from ..scopes.policies import ScopeClosePolicy
from ..scopes.scope import ProcessScope
from ..scopes.scope import ScopeCloseResult
from ..scopes.scope import ScopeManager
from ..spool.spool import OutputSpool
from ..spool.storage import SpoolStorage
from ..types.errors import ManagerClosedError
from ..types.errors import ManagerNotStartedError
from ..types.errors import ScopeClosedError
from ..types.errors import SpawnError
from ..types.errors import UnsafeChildSignalDispositionError
from ..types.events import ProcessEvent
from ..types.events import ProcessReparentedEvent
from ..types.events import ProcessSpawnedEvent
from ..types.events import ScopeClosedEvent
from ..types.events import ScopeOpenedEvent
from ..types.ids import CountingProcessIdGenerator
from ..types.ids import ProcessId
from ..types.ids import ProcessIdGenerator
from ..types.options import ProcessOptions
from ..types.options import Sandbox
from ..types.options import Target
from ..types.options import get_session_mode
from ..types.options import get_spool_policy
from ..types.specs import ProcessSpec
from ..types.specs import PtyStdio
from ..types.states import ProcessState
from . import pty as _pty
from .notifier import AsyncioSpoolNotifier
from .pipes import ReadPipeProtocol
from .pipes import StdinWriter
from .pipes import WritePipeProtocol
from .process import AsyncioProcess
from .spawn import _SpawnerPopen
from .spawn import spawn_popen


log = logs.get_module_logger(globals())


##


class _StatusProtocol(asyncio.Protocol):
    """Collects the exec-status pipe: EOF with nothing == exec happened; any bytes == a marshal'd shim error."""

    def __init__(self, fut: asyncio.Future[bytes]) -> None:
        super().__init__()

        self._fut = fut
        self._buf = bytearray()

    def data_received(self, data: bytes) -> None:
        self._buf += data

    def connection_lost(self, exc: BaseException | None) -> None:
        if not self._fut.done():
            self._fut.set_result(bytes(self._buf))


##


class AsyncioProcessManager(ProcessManager, ScopeManager):
    def __init__(
            self,
            config: ManagerConfig | None = None,
            *,
            launcher: Launcher | None = None,
            id_generator: ProcessIdGenerator | None = None,
    ) -> None:
        super().__init__()

        self._config = config if config is not None else ManagerConfig()
        self._launcher = launcher if launcher is not None else ShimLauncher(python=self._config.shim_python)
        self._ids = id_generator if id_generator is not None else CountingProcessIdGenerator()

        self._state: ta.Literal['new', 'started', 'closing', 'closed'] = 'new'
        self._loop: asyncio.AbstractEventLoop | None = None

        self._processes: dict[ProcessId, AsyncioProcess] = {}
        self._tasks: set[asyncio.Task] = set()

        # Spools are owned by their handles, not the manager: a spool is released (memory dropped, spill fd closed,
        # spill file unlinked unless kept) when it is explicitly closed - `ProcessScope.run` and the exec/tool paths do
        # so once they have collected the output - or, as a backstop, when the last reference to it goes away. The
        # manager only tracks them weakly, to sweep whatever is still alive at close.
        self._spools: weakref.WeakSet[OutputSpool] = weakref.WeakSet()
        self._any_spill_kept = False

        # Events are published strictly in the order they were raised, from one drain task, whether they came from a
        # sync callback (exit watcher, reparent) or an async path.
        self._event_queue: collections.deque[ProcessEvent] = collections.deque()
        self._drain_task: asyncio.Task | None = None

        self._spill_dir: str | None = None
        self._own_spill_dir = False

        self._root = ProcessScope(
            'root',
            parent=None,
            manager=self,
            options=self._config.default_options,
            close_policy=self._config.close_policy,
        )

    def __repr__(self) -> str:
        return lang.attr_repr(self, '_state', with_id=True)

    def __del__(self) -> None:
        if self._state == 'started':
            log.error(
                'processes: %r deleted without being closed! live processes: %r',
                self,
                list(self._processes.values()),
            )

    #

    @property
    def config(self) -> ManagerConfig:
        return self._config

    @property
    def root(self) -> ProcessScope:
        return self._root

    @property
    def processes(self) -> ta.Mapping[ProcessId, Process]:
        return types.MappingProxyType(self._processes)

    @property
    def started(self) -> bool:
        return self._state != 'new'

    @property
    def closed(self) -> bool:
        return self._state == 'closed'

    @property
    def spill_dir(self) -> str | None:
        return self._spill_dir

    def _check_started(self) -> None:
        if self._state == 'new':
            raise ManagerNotStartedError
        if self._state in ('closing', 'closed'):
            raise ManagerClosedError

    #

    @staticmethod
    def check_child_signal_disposition() -> None:
        """
        If SIGCHLD is ignored the kernel auto-reaps children and `waitid`/`waitpid` fail with ECHILD - pids would be
        recyclable the instant a child exits and nothing could be signaled safely. Refuse to run in such a process.
        """

        h = signal.getsignal(signal.SIGCHLD)
        if h is signal.SIG_IGN:
            raise UnsafeChildSignalDispositionError('SIGCHLD is SIG_IGN in this process')

        # A live check catches SA_NOCLDWAIT and foreign C-level handlers too.
        p = _SpawnerPopen(
            ['sh', '-c', ':'],
            stdin=subprocess.DEVNULL,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            start_new_session=True,
        )
        try:
            os.waitid(os.P_PID, p.pid, os.WEXITED | os.WNOWAIT)
            _, status = os.waitpid(p.pid, 0)
        except ChildProcessError as e:
            raise UnsafeChildSignalDispositionError(f'children are auto-reaped in this process: {e!r}') from e
        p.returncode = os.waitstatus_to_exitcode(status)

    async def start(self) -> None:
        check.state(self._state == 'new')
        self._loop = asyncio.get_running_loop()

        self.check_child_signal_disposition()

        if isinstance(self._launcher, ShimLauncher):
            self._launcher.validate()

        if (sd := self._config.spill_dir) is not None:
            os.makedirs(sd, exist_ok=True)
            self._spill_dir = sd
        else:
            self._spill_dir = tempfile.mkdtemp(prefix='om-processes-')
            self._own_spill_dir = True

        self._state = 'started'
        self._publish_soon(ScopeOpenedEvent(scope_path=tuple(self._root.path)))

    #

    async def _drain_events(self) -> None:
        try:
            while self._event_queue:
                e = self._event_queue.popleft()
                try:
                    await self._publish(e)
                except Exception:  # noqa
                    log.exception('processes: error publishing event %r', e)
        finally:
            self._drain_task = None
            if self._event_queue:
                # Raced with a late enqueue.
                self._ensure_drain()

    def _ensure_drain(self) -> None:
        if self._drain_task is None or self._drain_task.done():
            loop = check.not_none(self._loop)
            self._drain_task = t = loop.create_task(self._drain_events())
            self._tasks.add(t)
            t.add_done_callback(self._tasks.discard)

    def _publish_soon(self, event: ProcessEvent) -> None:
        self._event_queue.append(event)
        if self._loop is not None:
            self._ensure_drain()

    async def _publish_now(self, event: ProcessEvent) -> None:
        """Enqueues in order and waits until it (and everything before it) has been delivered."""

        self._publish_soon(event)
        while self._event_queue or (self._drain_task is not None and not self._drain_task.done()):
            if (t := self._drain_task) is None:
                self._ensure_drain()
                continue
            if t is asyncio.current_task():
                return
            await asyncio.shield(t)

    def _release_storage(self, storage: SpoolStorage) -> None:
        """Backstop release of a spool nobody closed: runs when its `OutputSpool` is garbage collected."""

        try:
            storage.close()
        except Exception:  # noqa
            log.exception('processes: error releasing spool storage %r', storage)
        if storage.spill_path is not None:
            self._any_spill_kept = True

    def _process_finished(self, process: AsyncioProcess) -> None:
        self._processes.pop(process.id, None)
        process.scope._unregister(process)  # noqa

    def _spawn_task(self, coro: ta.Coroutine[ta.Any, ta.Any, ta.Any]) -> None:
        loop = check.not_none(self._loop)
        t = loop.create_task(coro)
        self._tasks.add(t)
        t.add_done_callback(self._tasks.discard)

    #

    def scope_opened(self, scope: ProcessScope) -> None:
        if self._state == 'new':
            # The root scope, created in __init__ - announced from start().
            return
        self._publish_soon(ScopeOpenedEvent(scope_path=tuple(scope.path)))

    async def scope_closed(self, scope: ProcessScope, result: ScopeCloseResult) -> None:
        if self._loop is None:
            return
        await self._publish_now(ScopeClosedEvent(
            scope_path=tuple(scope.path),
            num_processes=result.num_processes,
            num_abandoned=result.num_abandoned,
        ))

    def reparent(self, process: Process, new_scope: ProcessScope) -> None:
        proc = check.isinstance(process, AsyncioProcess)
        old = proc.scope
        old._unregister(proc)  # noqa
        proc._set_scope(new_scope)  # noqa
        new_scope._register(proc)  # noqa
        self._publish_soon(ProcessReparentedEvent(
            process_id=proc.id,
            pid=proc.pid,
            scope_path=tuple(new_scope.path),
            old_scope_path=tuple(old.path),
        ))

    async def close_processes(
            self,
            processes: ta.Sequence[Process],
            policy: ScopeClosePolicy,
    ) -> ScopeCloseResult:
        if not processes:
            return ScopeCloseResult(num_processes=0)

        loop = check.not_none(self._loop)
        errors: list[Exception] = []

        async def one(p: Process) -> None:
            try:
                await p.aclose()
            except Exception as e:  # noqa
                errors.append(e)

        tasks = [loop.create_task(one(p)) for p in processes]
        try:
            async with asyncio.timeout(policy.overall_timeout_s):
                await asyncio.gather(*tasks)
        except TimeoutError:
            for t in tasks:
                t.cancel()
            await asyncio.gather(*tasks, return_exceptions=True)
            # Out of time: SIGKILL whatever is left and abandon it (its lingering watcher reaps it when it dies); a
            # handle that had already exited is simply reaped.
            for p in processes:
                if not p.state.is_terminal:
                    check.isinstance(p, AsyncioProcess)._abandon(  # noqa
                        f'scope close exceeded {policy.overall_timeout_s}s',
                        kill=True,
                    )

        return ScopeCloseResult(
            num_processes=len(processes),
            num_abandoned=sum(1 for p in processes if p.state is ProcessState.ABANDONED),
            errors=errors,
        )

    #

    async def spawn(self, scope: ProcessScope, spec: ProcessSpec, options: ProcessOptions) -> Process:
        self._check_started()
        loop = check.not_none(self._loop)

        pid_id = self._ids.next_id()

        # A Target (e.g. docker exec) rewrites the spec into the local command that reaches the destination; a Sandbox
        # (bwrap / sandbox-exec) then wraps it in local OS-level confinement.
        if (target := options.get(Target)) is not None:  # type: ignore[type-abstract]
            spec = target.transform_spec(spec)
        if (sandbox := options.get(Sandbox)) is not None:  # type: ignore[type-abstract]
            spec = sandbox.transform_spec(spec)

        stdio = spec.stdio
        spool_policy = get_spool_policy(options)
        session_mode = get_session_mode(options).mode

        # Our ends of the pipes; the child ends are handed to Popen and closed in the parent right after.
        parent_fds: list[int] = []
        child_fds: list[int] = []

        def _pipe(*, child_reads: bool) -> tuple[int, int]:
            r, w = os.pipe()
            if child_reads:
                child_fds.append(r)
                parent_fds.append(w)
                return r, w
            child_fds.append(w)
            parent_fds.append(r)
            return w, r

        def _close_all(fds: ta.Iterable[int]) -> None:
            for fd in fds:
                try:
                    os.close(fd)
                except OSError:
                    pass

        stdin_arg: ta.Any
        stdout_arg: ta.Any
        stderr_arg: ta.Any
        stdin_w: int | None = None
        stdout_r: int | None = None
        stderr_r: int | None = None

        is_pty = isinstance(stdio, PtyStdio)
        pty_master_fd: int | None = None
        pty_read_fd: int | None = None
        pty_write_fd: int | None = None

        # PtyStdio.term is authoritative for a pty we create: it overrides any inherited host TERM, and is only skipped
        # when the caller explicitly set TERM in spec.env.
        if (
                isinstance(stdio, PtyStdio) and
                stdio.term is not None and
                (spec.env is None or 'TERM' not in spec.env)
        ):
            spec = spec.with_env(TERM=stdio.term)

        try:
            if isinstance(stdio, PtyStdio):
                # A pty needs the child to be a session leader to acquire the slave as its controlling terminal.
                session_mode = 'session'
                master, slave = _pty.open_pty()
                parent_fds.append(master)
                child_fds.append(slave)
                _pty.set_winsize(slave, stdio.rows, stdio.cols)
                pty_read_fd = os.dup(master)
                os.set_inheritable(pty_read_fd, False)
                parent_fds.append(pty_read_fd)
                pty_write_fd = os.dup(master)
                os.set_inheritable(pty_write_fd, False)
                parent_fds.append(pty_write_fd)
                pty_master_fd = master
                stdin_arg = stdout_arg = stderr_arg = slave

            else:
                if stdio.stdin == 'pipe':
                    stdin_arg, stdin_w = _pipe(child_reads=True)
                elif stdio.stdin == 'devnull':
                    stdin_arg = subprocess.DEVNULL
                elif stdio.stdin == 'inherit':
                    stdin_arg = None
                else:
                    stdin_arg = check.isinstance(stdio.stdin, int)

                if stdio.stdout == 'pipe':
                    stdout_arg, stdout_r = _pipe(child_reads=False)
                elif stdio.stdout == 'devnull':
                    stdout_arg = subprocess.DEVNULL
                elif stdio.stdout == 'inherit':
                    stdout_arg = None
                else:
                    stdout_arg = check.isinstance(stdio.stdout, int)

                if stdio.stderr == 'pipe':
                    stderr_arg, stderr_r = _pipe(child_reads=False)
                elif stdio.stderr == 'devnull':
                    stderr_arg = subprocess.DEVNULL
                elif stdio.stderr == 'inherit':
                    stderr_arg = None
                elif stdio.stderr == 'stdout':
                    stderr_arg = subprocess.STDOUT
                else:
                    stderr_arg = check.isinstance(stdio.stderr, int)

            status_r, status_w = os.pipe()
            parent_fds.append(status_r)
            child_fds.append(status_w)

            plan = self._launcher.plan(spec, options, status_fd=status_w)
            try:
                popen = spawn_popen(
                    plan,
                    stdin=stdin_arg,
                    stdout=stdout_arg,
                    stderr=stderr_arg,
                    session_mode=session_mode,
                )
            except OSError as e:
                raise SpawnError('popen', e.errno, str(e), argv=list(spec.argv)) from e
            finally:
                plan.close()
                _close_all(child_fds)
                child_fds.clear()

        except BaseException:
            _close_all(child_fds)
            _close_all(parent_fds)
            raise

        # From here the child exists: whatever happens, it must end up managed and eventually reaped. Its handle and
        # exit watcher are set up synchronously right here; everything below that can suspend (pipe connects, the exec
        # handshake, the spawned event) runs inside one try whose handlers tear the handle down - in the background if
        # this task is being cancelled.

        storage = SpoolStorage(
            memory_cap=spool_policy.memory_cap,
            spill_dir=self._spill_dir if spool_policy.spill else None,
            spill_name=f'{pid_id}.spool',
            keep_spill=spool_policy.keep_spill,
        )
        spool = OutputSpool(storage, AsyncioSpoolNotifier(loop))
        self._spools.add(spool)
        weakref.finalize(spool, self._release_storage, storage)

        proc = AsyncioProcess(
            id=pid_id,
            spec=plan.spec,
            options=options,
            scope=scope,
            popen=popen,
            spool=spool,
            stdin=None,
            pty_master_fd=pty_master_fd,
            owner=self,
            loop=loop,
        )
        proc._start_watcher()  # noqa

        if is_pty:
            stdin_w = pty_write_fd
            output_reads: list[tuple[int, int]] = [(_pty.PTY_OUTPUT_FD, check.not_none(pty_read_fd))]
        else:
            output_reads = [(fd, r) for fd, r in ((1, stdout_r), (2, stderr_r)) if r is not None]

        # Raw parent fds not yet handed to a transport (the pty master is the handle's own). Whatever is still pending
        # when we bail is closed by hand; an fd wrapped in a file object is closed by its transport (or, if the connect
        # never completed, by the file object itself).
        pending_fds = [fd for fd in parent_fds if fd != pty_master_fd]

        def _adopt(fd: int, mode: str) -> ta.IO:
            pending_fds.remove(fd)
            return open(fd, mode, buffering=0)  # noqa

        try:
            if stdin_w is not None:
                w_transport, w_protocol = await loop.connect_write_pipe(
                    WritePipeProtocol,
                    _adopt(stdin_w, 'wb'),
                )
                proc._set_stdin(StdinWriter(w_transport, w_protocol))  # noqa

            for fd_num, parent_fd in output_reads:
                r_transport, _ = await loop.connect_read_pipe(
                    functools.partial(
                        ReadPipeProtocol,
                        functools.partial(proc._on_data, fd_num),  # noqa
                        functools.partial(proc._on_output_eof, fd_num),  # noqa
                    ),
                    _adopt(parent_fd, 'rb'),
                )
                proc._add_read_transport(fd_num, r_transport)  # noqa
            proc._no_output()  # noqa

            status_fut: asyncio.Future[bytes] = loop.create_future()
            await loop.connect_read_pipe(
                functools.partial(_StatusProtocol, status_fut),
                _adopt(status_r, 'rb'),
            )

            # The scope may have begun closing while the pipes were connecting - its close has already snapshotted its
            # processes, so registering now would leave this one in a closed scope with nothing to ever tear it down.
            if scope.closing:
                raise ScopeClosedError('/'.join(scope.path))
            scope._register(proc)  # noqa
            self._processes[pid_id] = proc

            try:
                status = await asyncio.wait_for(status_fut, self._config.spawn_timeout_s)
            except TimeoutError:
                raise SpawnError(
                    'handshake',
                    errno.ETIMEDOUT,
                    f'no exec status within {self._config.spawn_timeout_s}s',
                    argv=list(spec.argv),
                ) from None

            if status:
                try:
                    stage, err_no, msg = marshal.loads(status)  # noqa: S302
                except Exception:  # noqa
                    stage, err_no, msg = 'status', None, repr(status)
                raise SpawnError(str(stage), err_no, str(msg), argv=list(spec.argv))

            proc._mark_running()  # noqa

            # Registered, but the scope started closing during the handshake: it is being torn down by the scope's
            # close, so don't hand it out (the aclose below just joins that teardown).
            if scope.closing:
                raise ScopeClosedError('/'.join(scope.path))

            await self._publish_now(ProcessSpawnedEvent(
                process_id=proc.id,
                pid=proc.pid,
                scope_path=tuple(scope.path),
                argv=tuple(plan.spec.argv),
                name=spec.name,
            ))

        except asyncio.CancelledError:
            # The spawner is being cancelled - tear the child down in the background rather than leave it unmanaged.
            _close_all(pending_fds)
            self._spawn_task(proc.aclose())
            raise

        except BaseException:
            # The child is (or will shortly be) dead or unwanted: fully close it before surfacing the error.
            _close_all(pending_fds)
            await proc.aclose()
            raise

        return proc

    #

    async def aclose(self) -> None:
        if self._state == 'closed':
            return
        if self._state == 'new':
            self._state = 'closed'
            return
        # NOTE: deliberately no early return on 'closing': a concurrent (or previously cancelled) close must also run to
        # completion. Every step below is idempotent and safe to run concurrently.
        self._state = 'closing'

        errors: list[Exception] = []
        try:
            await self._root.aclose()
        except Exception as e:  # noqa
            errors.append(e)

        while self._tasks or self._event_queue:
            if self._event_queue:
                self._ensure_drain()
            await asyncio.gather(*list(self._tasks), return_exceptions=True)

        # The first closer to get here finishes up (this block does not suspend, so concurrent closers cannot
        # interleave in it).
        if self._state != 'closed':
            any_kept = self._any_spill_kept
            for sp in list(self._spools):
                try:
                    sp.close()
                except Exception as e:  # noqa
                    errors.append(e)
                if sp.spill_path is not None:
                    any_kept = True
            self._spools.clear()

            if self._own_spill_dir and self._spill_dir is not None and not any_kept:
                shutil.rmtree(self._spill_dir, ignore_errors=True)

            self._state = 'closed'

        if errors:
            if len(errors) == 1:
                raise errors[0]
            raise ExceptionGroup('Errors closing process manager', errors)
