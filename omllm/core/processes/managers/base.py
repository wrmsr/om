"""
`BaseProcessManager`: everything about being a process manager that does not depend on the async runtime - the
lifecycle, the registry and root scope, spawning (stdio / pty plumbing, the launcher plan, `spawn_child`, the
exec-status handshake, registration), the ordered event stream, scope hooks, teardown and the spill directory. Handles
are `BaseProcess`es, which are equally runtime-agnostic.

What an implementation supplies is deliberately narrow, and named `_..._runtime`-ish below: an `Asynclite` for events
and locks, task spawning / joining, a bounded concurrent run (for scope close), a spool notifier, the process handle
subclass (which knows how to post callbacks from the exit-watcher thread), and the three pipe connections (stdin writer,
output readers, the exec-status pipe). See `../asyncio/manager.py` for the only implementation today.
"""
import abc
import collections
import contextvars
import errno
import os
import shutil
import signal
import tempfile
import types
import typing as ta
import weakref

from omcore import check
from omcore import lang
from omcore.asyncs.asynclite import all as asl
from omcore.logs import all as logs

from ..handles import Process
from ..launch.launcher import Launcher
from ..launch.shim import ShimLauncher
from ..launch.shim import decode_shim_status
from ..scopes.policies import ScopeClosePolicy
from ..scopes.scope import ProcessScope
from ..scopes.scope import ScopeCloseResult
from ..scopes.scope import ScopeManager
from ..spool.spool import OutputSpool
from ..spool.spool import SpoolNotifier
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
from .process import BaseProcess
from .process import ProcessStdinWriter
from .spawn import make_control_socketpair
from .spawn import send_control_fds
from .spawn import spawn_child
from .stdio import close_fds_quietly
from .stdio import setup_stdio
from .types import ManagerConfig
from .types import ProcessManager


log = logs.get_module_logger(globals())


##


# Set while a task is inside `_drain_events`, so a subscriber that publishes from within its own callback does not wait
# on the very drain it is running in.
_IN_DRAIN: contextvars.ContextVar[bool] = contextvars.ContextVar('om_processes_in_drain', default=False)


class BaseProcessManager(ProcessManager, ScopeManager, lang.Abstract):
    def __init__(
            self,
            config: ManagerConfig | None = None,
            *,
            asynclite: asl.All,
            launcher: Launcher | None = None,
            id_generator: ProcessIdGenerator | None = None,
    ) -> None:
        super().__init__()

        self._config = config if config is not None else ManagerConfig()
        self._asynclite = asynclite
        self._launcher = launcher if launcher is not None else ShimLauncher(python=self._config.shim_python)
        self._ids = id_generator if id_generator is not None else CountingProcessIdGenerator()

        self._state: ta.Literal['new', 'started', 'closing', 'closed'] = 'new'
        self._runtime_ready = False
        self._posix_spawn_setsid: bool | None = None

        self._processes: dict[ProcessId, BaseProcess] = {}

        # Spools are owned by their handles, not the manager: a spool is released (memory dropped, spill fd closed,
        # spill file unlinked unless kept) when it is explicitly closed - `ProcessScope.run` and the exec/tool paths do
        # so once they have collected the output - or, as a backstop, when the last reference to it goes away. The
        # manager only tracks them weakly, to sweep whatever is still alive at close.
        self._spools: weakref.WeakSet[OutputSpool] = weakref.WeakSet()
        self._any_spill_kept = False

        # Events are published strictly in the order they were raised, from one drain task at a time, whether they came
        # from a sync callback (exit watcher, reparent) or an async path.
        self._event_queue: collections.deque[ProcessEvent] = collections.deque()
        self._draining = False
        self._drain_idle = asynclite.make_event()
        self._drain_idle.set()

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

    ##
    # Runtime hooks - the only thing an implementation provides.

    @abc.abstractmethod
    def _start_runtime(self) -> ta.Awaitable[None]:
        """Called first thing in `start()`, from the context every later async call will be made from."""

        raise NotImplementedError

    @abc.abstractmethod
    def _spawn_task(self, coro: ta.Coroutine[ta.Any, ta.Any, ta.Any]) -> None:
        """
        Runs `coro` in the background, tracked until it finishes (see `_join_tasks`). Never raises into the caller.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def _join_tasks(self) -> ta.Awaitable[None]:
        """Waits until no background task spawned via `_spawn_task` remains."""

        raise NotImplementedError

    @abc.abstractmethod
    def _run_all_bounded(
            self,
            coros: ta.Sequence[ta.Coroutine[ta.Any, ta.Any, ta.Any]],
            timeout: float | None,
    ) -> ta.Awaitable[bool]:
        """
        Runs the coroutines concurrently. Returns True once all have finished; if `timeout` expires first, cancels /
        abandons the stragglers and returns False. Exceptions from the coroutines are the coroutines' own business (the
        callers wrap them).
        """

        raise NotImplementedError

    @abc.abstractmethod
    def _new_spool_notifier(self) -> SpoolNotifier:
        raise NotImplementedError

    @abc.abstractmethod
    def _new_process(self, **kwargs: ta.Any) -> BaseProcess:
        """Constructs the implementation's `BaseProcess` subclass; `kwargs` are exactly `BaseProcess.__init__`'s."""

        raise NotImplementedError

    @abc.abstractmethod
    def _connect_stdin(self, fd: int) -> ta.Awaitable[ProcessStdinWriter]:
        """
        Takes ownership of our write end `fd` of the child's stdin (or the pty master dup) - closing it on failure.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def _connect_output(self, process: BaseProcess, fd_num: int, fd: int) -> ta.Awaitable[None]:
        """
        Takes ownership of our read end `fd` of an output pipe (or the pty master dup), streaming into
        `process._on_data(fd_num, ...)` / `process._on_output_eof(fd_num, ...)` and registering its closer via
        `process._add_output_channel(fd_num, ...)`.
        """

        raise NotImplementedError

    @abc.abstractmethod
    def _read_exec_status(self, fd: int, timeout: float) -> ta.Awaitable[bytes | None]:
        """
        Takes ownership of `fd`, our end of the child's control socket, and returns everything the child writes to it up
        to EOF (an empty bytes == the exec happened), or None if that does not happen within `timeout` (the socket is
        then left to close itself once the child dies).
        """

        raise NotImplementedError

    ##

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
    def check_child_signal_disposition() -> bool:
        """
        If SIGCHLD is ignored the kernel auto-reaps children and `waitid`/`waitpid` fail with ECHILD - pids would be
        recyclable the instant a child exits and nothing could be signaled safely. Refuse to run in such a process.
        Returns whether this Python build can ask `posix_spawn` to create a new session.
        """

        h = signal.getsignal(signal.SIGCHLD)
        if h is signal.SIG_IGN:
            raise UnsafeChildSignalDispositionError('SIGCHLD is SIG_IGN in this process')

        # A live check catches SA_NOCLDWAIT and foreign C-level handlers too.
        devnull = os.open(os.devnull, os.O_RDWR)
        try:
            try:
                pid = spawn_child(
                    ['sh', '-c', ':'],
                    stdin_fd=devnull,
                    stdout_fd=devnull,
                    stderr_fd=devnull,
                    session_mode='session',
                )
            except NotImplementedError:
                posix_spawn_setsid = False
                # The child-disposition check itself does not require a session. A real session launch will ask the
                # shim to call setsid before target exec.
                pid = spawn_child(
                    ['sh', '-c', ':'],
                    stdin_fd=devnull,
                    stdout_fd=devnull,
                    stderr_fd=devnull,
                )
            else:
                posix_spawn_setsid = True
        finally:
            os.close(devnull)
        try:
            os.waitid(os.P_PID, pid, os.WEXITED | os.WNOWAIT)
            os.waitpid(pid, 0)
        except ChildProcessError as e:
            raise UnsafeChildSignalDispositionError(f'children are auto-reaped in this process: {e!r}') from e
        return posix_spawn_setsid

    async def start(self) -> None:
        check.state(self._state == 'new')
        await self._start_runtime()
        self._runtime_ready = True

        self._posix_spawn_setsid = self.check_child_signal_disposition()

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

    ##
    # Events

    async def _drain_events(self) -> None:
        tok = _IN_DRAIN.set(True)
        try:
            while self._event_queue:
                e = self._event_queue.popleft()
                try:
                    await self._publish(e)
                except Exception:  # noqa
                    log.exception('processes: error publishing event %r', e)
        finally:
            _IN_DRAIN.reset(tok)
            self._draining = False
            self._drain_idle.set()
            if self._event_queue:
                # Raced with a late enqueue.
                self._ensure_drain()

    def _ensure_drain(self) -> None:
        if self._draining or not self._runtime_ready:
            return
        self._draining = True
        # A fresh idle event per drain: everyone waiting on the previous one has been released.
        self._drain_idle = self._asynclite.make_event()
        self._spawn_task(self._drain_events())

    def _publish_soon(self, event: ProcessEvent) -> None:
        self._event_queue.append(event)
        self._ensure_drain()

    async def _publish_now(self, event: ProcessEvent) -> None:
        """Enqueues in order and waits until it (and everything before it) has been delivered."""

        self._publish_soon(event)
        if _IN_DRAIN.get():
            # Published from within a subscriber: the running drain will get to it - waiting would deadlock.
            return
        while self._event_queue or self._draining:
            if not self._draining:
                self._ensure_drain()
                continue
            await self._drain_idle.wait()

    ##
    # Handle callbacks

    def _release_storage(self, storage: SpoolStorage) -> None:
        """Backstop release of a spool nobody closed: runs when its `OutputSpool` is garbage collected."""

        try:
            storage.close()
        except Exception:  # noqa
            log.exception('processes: error releasing spool storage %r', storage)
        if storage.spill_path is not None:
            self._any_spill_kept = True

    def _process_finished(self, process: BaseProcess) -> None:
        self._processes.pop(process.id, None)
        process.scope._unregister(process)  # noqa

    ##
    # Scope hooks

    def scope_opened(self, scope: ProcessScope) -> None:
        if self._state == 'new':
            # The root scope, created in __init__ - announced from start().
            return
        self._publish_soon(ScopeOpenedEvent(scope_path=tuple(scope.path)))

    async def scope_closed(self, scope: ProcessScope, result: ScopeCloseResult) -> None:
        if not self._runtime_ready:
            return
        await self._publish_now(ScopeClosedEvent(
            scope_path=tuple(scope.path),
            num_processes=result.num_processes,
            num_abandoned=result.num_abandoned,
        ))

    def reparent(self, process: Process, new_scope: ProcessScope) -> None:
        proc = check.isinstance(process, BaseProcess)
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

        errors: list[Exception] = []

        async def one(p: Process) -> None:
            try:
                await p.aclose()
            except Exception as e:  # noqa
                errors.append(e)

        if not await self._run_all_bounded([one(p) for p in processes], policy.overall_timeout_s):
            # Out of time: SIGKILL whatever is left and abandon it (its lingering watcher reaps it when it dies); a
            # handle that had already exited is simply reaped.
            for p in processes:
                if not p.state.is_terminal:
                    check.isinstance(p, BaseProcess)._abandon(  # noqa
                        f'scope close exceeded {policy.overall_timeout_s}s',
                        kill=True,
                    )

        return ScopeCloseResult(
            num_processes=len(processes),
            num_abandoned=sum(1 for p in processes if p.state is ProcessState.ABANDONED),
            errors=errors,
        )

    ##
    # Spawn

    async def spawn(self, scope: ProcessScope, spec: ProcessSpec, options: ProcessOptions) -> Process:
        self._check_started()

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

        # PtyStdio.term is authoritative for a pty we create: it overrides any inherited host TERM, and is only skipped
        # when the caller explicitly set TERM in spec.env.
        if (
                isinstance(stdio, PtyStdio) and
                stdio.term is not None and
                (spec.env is None or 'TERM' not in spec.env)
        ):
            spec = spec.with_env(TERM=stdio.term)

        sio = setup_stdio(stdio)
        if sio.is_pty:
            # A pty needs the child to be a session leader to acquire the slave as its controlling terminal.
            session_mode = 'session'

        # Some portable CPython builds (notably uv's python-build-standalone Linux interpreters) were compiled against
        # libc headers without POSIX_SPAWN_SETSID even when the runtime libc supports it. Spawn the shim without group
        # changes in that case; it will call setsid itself before the target can execute.
        child_setsid = session_mode == 'session' and not check.not_none(self._posix_spawn_setsid)
        spawn_session_mode = None if child_setsid else session_mode

        try:
            ctl_parent, ctl_child = make_control_socketpair()
        except BaseException:
            sio.close_all()
            raise

        try:
            plan = self._launcher.plan(spec, options, child_setsid=child_setsid)
            try:
                # Queued before the child exists: the payload blob and the caller's pass-fds travel as SCM_RIGHTS - the
                # only way anything but 0/1/2 and the control socket itself reaches the child.
                send_control_fds(ctl_parent, plan.send_fds)
                pid = spawn_child(
                    plan.argv,
                    env=plan.env,
                    stdin_fd=sio.stdin_fd,
                    stdout_fd=sio.stdout_fd,
                    stderr_fd=sio.stderr_fd,
                    control=(ctl_child.fileno(), plan.control_fd),
                    session_mode=spawn_session_mode,
                )
            except OSError as e:
                raise SpawnError('spawn', e.errno, str(e), argv=list(spec.argv)) from e
            finally:
                plan.close()

        except BaseException:
            # (Runs before the `finally` below - together they close everything exactly once.)
            ctl_parent.close()
            close_fds_quietly(sio.parent_fds)
            raise

        finally:
            # The child's ends are its own now (or it never came to be): ours to close either way.
            ctl_child.close()
            close_fds_quietly(sio.child_fds)

        # From here on the parent end of the control socket is just an fd: the exec-status channel.
        status_r = ctl_parent.detach()

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
        spool = OutputSpool(storage, self._new_spool_notifier())
        self._spools.add(spool)
        weakref.finalize(spool, self._release_storage, storage)

        proc = self._new_process(
            id=pid_id,
            spec=plan.spec,
            options=options,
            scope=scope,
            pid=pid,
            spool=spool,
            pty_master_fd=sio.pty_master_fd,
            process_group_ready=not child_setsid,
            owner=self,
            asynclite=self._asynclite,
        )
        proc._start_watcher()  # noqa

        # Raw parent fds not yet handed to a connection (the pty master is the handle's own). Whatever is still pending
        # when we bail is closed by hand; a connection hook owns its fd from the moment it is called.
        pending_fds = [fd for fd in (*sio.parent_fds, status_r) if fd != sio.pty_master_fd]

        def _take(fd: int) -> int:
            pending_fds.remove(fd)
            return fd

        try:
            if sio.stdin_w is not None:
                proc._set_stdin(await self._connect_stdin(_take(sio.stdin_w)))  # noqa

            for fd_num, parent_fd in sio.output_reads:
                await self._connect_output(proc, fd_num, _take(parent_fd))
            proc._no_output()  # noqa

            # The scope may have begun closing while the pipes were connecting - its close has already snapshotted its
            # processes, so registering now would leave this one in a closed scope with nothing to ever tear it down.
            if scope.closing:
                raise ScopeClosedError('/'.join(scope.path))
            scope._register(proc)  # noqa
            self._processes[pid_id] = proc

            status = await self._read_exec_status(_take(status_r), self._config.spawn_timeout_s)
            if status is None:
                raise SpawnError(
                    'handshake',
                    errno.ETIMEDOUT,
                    f'no exec status within {self._config.spawn_timeout_s}s',
                    argv=list(spec.argv),
                )
            if status:
                stage, err_no, msg = decode_shim_status(status)
                raise SpawnError(stage, err_no, msg, argv=list(spec.argv))

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

        except Exception:
            # The child is (or will shortly be) dead or unwanted: fully close it before surfacing the error.
            close_fds_quietly(pending_fds)
            await proc.aclose()
            raise

        except BaseException:
            # Cancellation (or worse): we cannot await here - tear the child down in the background rather than leave
            # it unmanaged.
            close_fds_quietly(pending_fds)
            self._spawn_task(proc.aclose())
            raise

        return proc

    ##
    # Close

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

        while True:
            if self._event_queue:
                self._ensure_drain()
            await self._join_tasks()
            if not self._event_queue and not self._draining:
                break

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
