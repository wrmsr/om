"""
The host side of remote process management: `RemoteProcessManager` implements the ordinary `ProcessManager` and
`ScopeManager` contracts over an rpc peer to a remote agent's `RemoteProcessService`, with local proxy handles
(`RemoteProcess`) and local output spools, so the exec and process tools need no remote-specific variants.

Output chunks, end of output, and exits arrive as notifications, applied inline in the peer's receive loop in wire
order: every chunk the agent sent before its reply to a `close` is in the spool by the time that reply is seen. Events
are published in the order they happened, from one drain, exactly like the local manager's. A spawn the caller cancels
still closes the child the agent forked for it as soon as its id is known, and a lost connection poisons every handle.
"""
import asyncio
import os
import shutil
import signal
import tempfile
import types
import typing as ta

from omcore import check
from omcore.asyncs.asynclite import all as asl
from omcore.lite.marshal import marshal_obj
from omcore.lite.marshal import unmarshal_obj
from omcore.logs import all as logs

from ...rpc.errors import RpcConnectionClosedError
from ...rpc.errors import RpcRemoteError
from ...rpc.handlers import RpcNotificationRouter
from ...rpc.peers import RpcPeer
from ...rpc.translate import translate_rpc_remote_builtin_error
from ..asyncio.notifier import AsyncioSpoolNotifier
from ..handles import Process
from ..managers.events import ProcessEventDrain
from ..managers.types import ManagerConfig
from ..managers.types import ProcessManager
from ..managers.types import RootProcessScope
from ..scopes.policies import ScopeClosePolicy
from ..scopes.scope import ProcessScope
from ..scopes.scope import ScopeCloseResult
from ..scopes.scope import ScopeManager
from ..spool.spool import OutputSpool
from ..spool.storage import SpoolStorage
from ..types.errors import ManagerClosedError
from ..types.errors import ManagerNotStartedError
from ..types.errors import NotAPtyError
from ..types.errors import ProcessNotAliveError
from ..types.errors import ProcessPoisonedError
from ..types.errors import ProcessTimeoutError
from ..types.errors import ScopeClosedError
from ..types.events import ProcessEvent
from ..types.events import ProcessExitedEvent
from ..types.events import ProcessPoisonedEvent
from ..types.events import ProcessReapedEvent
from ..types.events import ProcessReparentedEvent
from ..types.events import ProcessSpawnedEvent
from ..types.events import ScopeClosedEvent
from ..types.events import ScopeOpenedEvent
from ..types.ids import ProcessId
from ..types.options import ProcessOptions
from ..types.options import RunTimeout
from ..types.options import SessionMode
from ..types.options import SpoolPolicy
from ..types.options import Tag
from ..types.options import TerminationPolicy
from ..types.specs import ProcessSpec
from ..types.specs import PtyStdio
from ..types.specs import Stdio
from ..types.states import ProcessState
from .protocol import REMOTE_PROCESS_CLOSE_METHOD
from .protocol import REMOTE_PROCESS_EVENT_METHODS
from .protocol import REMOTE_PROCESS_EXITED_METHOD
from .protocol import REMOTE_PROCESS_OUTPUT_END_METHOD
from .protocol import REMOTE_PROCESS_OUTPUT_METHOD
from .protocol import REMOTE_PROCESS_RESIZE_METHOD
from .protocol import REMOTE_PROCESS_SIGNAL_METHOD
from .protocol import REMOTE_PROCESS_SPAWN_METHOD
from .protocol import REMOTE_PROCESS_WRITE_EOF_METHOD
from .protocol import REMOTE_PROCESS_WRITE_METHOD
from .protocol import RemoteProcessCloseParams
from .protocol import RemoteProcessClosePolicySpec
from .protocol import RemoteProcessCloseResult
from .protocol import RemoteProcessExitedEvent
from .protocol import RemoteProcessOutputEndEvent
from .protocol import RemoteProcessOutputEvent
from .protocol import RemoteProcessRefParams
from .protocol import RemoteProcessResizeParams
from .protocol import RemoteProcessSignalParams
from .protocol import RemoteProcessSpawnParams
from .protocol import RemoteProcessSpawnResult
from .protocol import RemoteProcessStdioSpec
from .protocol import RemoteProcessWriteParams


log = logs.get_module_logger(globals())


##


class RemoteProcess(Process):
    def __init__(
            self,
            *,
            manager: 'RemoteProcessManager',  # noqa: UP037
            process_id: ProcessId,
            pid: int,
            spec: ProcessSpec,
            options: ProcessOptions,
            scope: ProcessScope,
            created_at: float,
            spool: OutputSpool,
    ) -> None:
        super().__init__()

        self._manager = manager
        self._id = process_id
        self._pid = pid
        self._spec = spec
        self._options = options
        self._scope = scope
        self._created_at = created_at
        self._spool = spool

        self._state = ProcessState.RUNNING
        self._returncode: int | None = None
        self._exited = asyncio.Event()
        self._output_ended = asyncio.Event()
        self._stdin_closed = not self.has_stdin
        self._close_task: asyncio.Task[None] | None = None

        if isinstance(spec.stdio, PtyStdio):
            self._winsize: tuple[int, int] | None = (spec.stdio.rows, spec.stdio.cols)
        else:
            self._winsize = None

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

    def _set_scope(self, scope: ProcessScope) -> None:
        self._scope = scope

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def closing(self) -> bool:
        return self._close_task is not None and not self._close_task.done()

    @property
    def exited(self) -> bool:
        return self._exited.is_set() and self._state is not ProcessState.POISONED

    def _on_output(self, fd: int, data: bytes) -> None:
        if not self._spool.ended and not self._spool.storage.closed:
            self._spool.append(fd, data)

    def _on_output_end(self) -> None:
        self._spool.mark_ended()
        self._output_ended.set()

    def _on_exited(self, returncode: int) -> None:
        if self._state.is_terminal:
            return
        self._returncode = returncode
        self._state = ProcessState.EXITED
        self._exited.set()
        self._manager._publish_soon(ProcessExitedEvent(  # noqa
            process_id=self._id,
            pid=self._pid,
            scope_path=tuple(self._scope.path),
            returncode=returncode,
        ))

    def _on_reaped(self, returncode: int) -> None:
        if self._state.is_terminal:
            return
        self._returncode = returncode
        self._exited.set()
        self._state = ProcessState.REAPED
        self._on_output_end()
        self._stdin_closed = True
        self._manager._process_finished(self)  # noqa: SLF001
        self._manager._publish_soon(ProcessReapedEvent(  # noqa
            process_id=self._id,
            pid=self._pid,
            scope_path=tuple(self._scope.path),
            returncode=returncode,
        ))

    def _on_connection_lost(self, reason: str) -> None:
        if self._state.is_terminal:
            return
        self._state = ProcessState.POISONED
        self._exited.set()
        self._on_output_end()
        self._stdin_closed = True
        self._manager._process_finished(self)  # noqa: SLF001
        self._manager._publish_soon(ProcessPoisonedEvent(  # noqa
            process_id=self._id,
            pid=self._pid,
            scope_path=tuple(self._scope.path),
            reason=reason,
        ))

    async def wait(self, timeout: float | None = None) -> int:
        if not self._exited.is_set():
            if timeout is not None and timeout <= 0:
                raise ProcessTimeoutError(f'{self!r} did not exit within {timeout}s')
            try:
                await asyncio.wait_for(self._exited.wait(), timeout)
            except TimeoutError:
                raise ProcessTimeoutError(f'{self!r} did not exit within {timeout}s') from None
        if self._state is ProcessState.POISONED:
            raise ProcessPoisonedError(repr(self))
        return check.not_none(self._returncode)

    async def signal(self, sig: int, *, process_group: bool | None = None) -> None:
        if self._state.is_terminal:
            raise ProcessNotAliveError(repr(self))
        if process_group is None:
            process_group = self._options.get(
                TerminationPolicy,
                TerminationPolicy(),
            ).process_group
        await self._manager._call(  # noqa
            REMOTE_PROCESS_SIGNAL_METHOD,
            marshal_obj(RemoteProcessSignalParams(
                id=self._id,
                signal=int(sig),
                process_group=process_group,
            )),
        )

    async def terminate(self) -> None:
        policy = self._options.get(TerminationPolicy, TerminationPolicy())
        await self.signal(policy.signal)

    async def kill(self) -> None:
        await self.signal(signal.SIGKILL)

    @property
    def has_stdin(self) -> bool:
        if isinstance(self._spec.stdio, PtyStdio):
            return True
        return self._spec.stdio.stdin == 'pipe'

    @property
    def stdin_closed(self) -> bool:
        return self._stdin_closed

    async def write(self, data: bytes) -> None:
        if not self.has_stdin or self._stdin_closed:
            raise BrokenPipeError('process has no open stdin')
        await self._manager._call(  # noqa
            REMOTE_PROCESS_WRITE_METHOD,
            marshal_obj(RemoteProcessWriteParams(
                id=self._id,
                data=data,
            )),
        )

    async def write_eof(self) -> None:
        if self._stdin_closed:
            return
        await self._manager._call(  # noqa
            REMOTE_PROCESS_WRITE_EOF_METHOD,
            marshal_obj(RemoteProcessRefParams(
                id=self._id,
            )),
        )
        self._stdin_closed = True

    @property
    def spool(self) -> OutputSpool:
        return self._spool

    @property
    def output_ended(self) -> bool:
        return self._output_ended.is_set()

    async def wait_output_ended(self, timeout: float | None = None) -> bool:
        if self._output_ended.is_set():
            return True
        if timeout is not None and timeout <= 0:
            return False
        try:
            await asyncio.wait_for(self._output_ended.wait(), timeout)
        except TimeoutError:
            return self._output_ended.is_set()
        return True

    @property
    def has_pty(self) -> bool:
        return isinstance(self._spec.stdio, PtyStdio)

    async def resize(self, rows: int, cols: int) -> None:
        if not self.has_pty:
            raise NotAPtyError(repr(self))
        if self._state.is_terminal:
            raise ProcessNotAliveError(repr(self))
        await self._manager._call(  # noqa
            REMOTE_PROCESS_RESIZE_METHOD,
            marshal_obj(RemoteProcessResizeParams(id=self._id, rows=rows, cols=cols)),
        )
        self._winsize = (rows, cols)

    def get_winsize(self) -> tuple[int, int] | None:
        if self._state.is_terminal:
            return None
        return self._winsize

    async def aclose(
            self,
            policy: TerminationPolicy | None = None,
            *,
            wait_s: float | None = None,
    ) -> None:
        if self._state.is_terminal:
            return
        if self._close_task is None:
            if policy is None:
                policy = self._options.get(TerminationPolicy, TerminationPolicy())
            self._close_task = self._manager._start_close(self, policy)  # noqa
        # The teardown is the manager's task, not the caller's: a cancelled or timed-out wait leaves it running.
        if wait_s is None:
            await asyncio.shield(self._close_task)
        else:
            try:
                await asyncio.wait_for(asyncio.shield(self._close_task), wait_s)
            except TimeoutError:
                return


##


_REMOTE_PROCESS_SUPPORTED_OPTIONS: ta.Final = (
    TerminationPolicy,
    SpoolPolicy,
    SessionMode,
    RunTimeout,
    Tag,
)


class RemoteProcessManager(ProcessManager, ScopeManager):
    def __init__(
            self,
            peer: RpcPeer,
            *,
            notifications: RpcNotificationRouter,
            config: ManagerConfig | None = None,
    ) -> None:
        super().__init__()

        self._peer = peer
        self._config = config if config is not None else ManagerConfig()
        self._state: ta.Literal['new', 'started', 'closing', 'closed'] = 'new'
        self._processes: dict[ProcessId, RemoteProcess] = {}
        self._pending_events: dict[str, list[tuple[str, ta.Any]]] = {}
        self._retired_ids: set[str] = set()
        self._tasks: set[asyncio.Task] = set()
        self._spools: set[OutputSpool] = set()
        self._spill_dir: str | None = None
        self._own_spill_dir = False

        # Events are published strictly in the order they were raised, from one drain task at a time, whether they came
        # from a notification (exit, output end) or an async path.
        self._events = ProcessEventDrain(
            publish=self._publish,
            spawn_task=self._spawn_task,
            asynclite=asl.asyncio.All(),
        )

        self._root = RootProcessScope(ProcessScope(
            'root',
            parent=None,
            manager=self,
            options=self._config.default_options,
            close_policy=self._config.close_policy,
        ))

        # The agent's process events arrive as notifications, applied inline in the peer's receive loop in wire order;
        # and when the connection goes, so do the processes behind it.
        notifications.add_routes(REMOTE_PROCESS_EVENT_METHODS, self.handle_event)
        peer.add_close_callback(self._on_peer_closed)

    @property
    def config(self) -> ManagerConfig:
        return self._config

    @property
    def root(self) -> RootProcessScope:
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

    async def start(self) -> None:
        if self._state != 'new':
            raise RuntimeError(f'Cannot start remote process manager in state {self._state!r}')
        if self._config.spill_dir is not None:
            os.makedirs(self._config.spill_dir, exist_ok=True)
            self._spill_dir = self._config.spill_dir
        else:
            self._spill_dir = tempfile.mkdtemp(prefix='om-remote-processes-')
            self._own_spill_dir = True
        self._state = 'started'
        self._events.enable()

    ##
    # Tasks and events

    def _spawn_task(self, coro: ta.Coroutine[ta.Any, ta.Any, ta.Any]) -> None:
        task = asyncio.create_task(coro)
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)

    async def _join_tasks(self) -> None:
        while self._tasks:
            await asyncio.gather(*list(self._tasks), return_exceptions=True)
            # `gather` completes eagerly (without yielding) when every task is already done, and a finished task stays
            # in `_tasks` until its discard callback has run - so give the loop a turn to run those.
            await asyncio.sleep(0)

    def _publish_soon(self, event: ProcessEvent) -> None:
        self._events.publish_soon(event)

    ##
    # Remote calls

    async def _call(self, method: str, params: ta.Any) -> ta.Any:
        try:
            return await self._peer.call(method, params)
        except RpcRemoteError as e:
            raise translate_rpc_remote_builtin_error(e) from e

    @staticmethod
    def _close_policy_spec(policy: TerminationPolicy) -> RemoteProcessClosePolicySpec:
        return RemoteProcessClosePolicySpec(
            signal=int(policy.signal),
            grace_s=policy.grace_s,
            kill_s=policy.kill_s,
            close_stdin=policy.close_stdin,
            process_group=policy.process_group,
            drain_s=policy.drain_s,
        )

    def _process_finished(self, process: RemoteProcess) -> None:
        self._processes.pop(process.id, None)
        process.scope._unregister(process)  # noqa
        self._retired_ids.add(process.id)

    def _start_close(self, process: RemoteProcess, policy: TerminationPolicy) -> asyncio.Task[None]:
        async def run() -> None:
            try:
                r: RemoteProcessCloseResult = unmarshal_obj(
                    await self._call(
                        REMOTE_PROCESS_CLOSE_METHOD,
                        marshal_obj(RemoteProcessCloseParams(
                            id=process.id,
                            policy=self._close_policy_spec(policy),
                        )),
                    ),
                    RemoteProcessCloseResult,
                )
                if r.state != 'reaped':
                    raise RuntimeError(f'Unexpected remote process close state: {r.state!r}')
                process._on_reaped(r.returncode)  # noqa
            except RpcConnectionClosedError:
                process._on_connection_lost('RPC connection closed during process teardown')  # noqa
            except BaseException:
                process._on_connection_lost('remote process teardown failed')  # noqa
                raise

        task = asyncio.create_task(
            run(),
            name=f'remote-process-close-{process.id}',
        )
        self._tasks.add(task)
        task.add_done_callback(self._tasks.discard)
        return task

    def _close_orphan_spawn(self, spawn_call: asyncio.Future) -> None:
        """
        Runs when a spawn whose caller gave up on it (see `spawn`) completes: whatever process the agent did start is
        nobody's, and is closed right away.
        """

        if spawn_call.cancelled() or spawn_call.exception() is not None:
            return
        try:
            process_id: str = unmarshal_obj(spawn_call.result(), RemoteProcessSpawnResult).id
        except Exception:  # noqa
            return
        self._retired_ids.add(process_id)
        self._pending_events.pop(process_id, None)
        self._spawn_task(self._close_orphan(process_id))

    async def _close_orphan(self, process_id: str) -> None:
        try:
            await self._call(
                REMOTE_PROCESS_CLOSE_METHOD,
                marshal_obj(RemoteProcessCloseParams(
                    id=process_id,
                    policy=self._close_policy_spec(TerminationPolicy()),
                )),
            )
        except RpcConnectionClosedError:
            # The agent tears down everything it still has when the connection goes.
            pass
        except Exception:  # noqa
            log.exception('Error closing orphaned remote process %r', process_id)

    @staticmethod
    def _stdio_spec(stdio: Stdio) -> RemoteProcessStdioSpec:
        if isinstance(stdio, PtyStdio):
            return RemoteProcessStdioSpec(
                kind='pty',
                rows=stdio.rows,
                cols=stdio.cols,
                term=stdio.term,
            )

        for name, value in (
                ('stdin', stdio.stdin),
                ('stdout', stdio.stdout),
                ('stderr', stdio.stderr),
        ):
            if isinstance(value, int) or value == 'inherit':
                raise ValueError(f'Remote process stdio does not support {name}={value!r}')
        return RemoteProcessStdioSpec(
            kind='pipes',
            stdin=ta.cast(str, stdio.stdin),
            stdout=ta.cast(str, stdio.stdout),
            stderr=ta.cast(str, stdio.stderr),
        )

    async def spawn(
            self,
            scope: ProcessScope,
            spec: ProcessSpec,
            options: ProcessOptions,
    ) -> Process:
        if self._state != 'started':
            if self.closed:
                raise ManagerClosedError
            raise ManagerNotStartedError
        unsupported = [
            option
            for option in options
            if not isinstance(option, _REMOTE_PROCESS_SUPPORTED_OPTIONS)
        ]
        if unsupported:
            raise ValueError(f'Unsupported remote process options: {unsupported!r}')
        if (
                (session_mode := options.get(SessionMode)) is not None and
                session_mode.mode != 'session'
        ):
            raise ValueError(f'Unsupported remote process session mode: {session_mode.mode!r}')

        spawn_call = asyncio.ensure_future(
            self._call(
                REMOTE_PROCESS_SPAWN_METHOD,
                marshal_obj(RemoteProcessSpawnParams(
                    argv=list(spec.argv),
                    cwd=spec.cwd,
                    env=dict(spec.env) if spec.env is not None else None,
                    stdio=self._stdio_spec(spec.stdio),
                    name=spec.name,
                )),
            ),
        )
        try:
            obj: RemoteProcessSpawnResult = unmarshal_obj(await asyncio.shield(spawn_call), RemoteProcessSpawnResult)
        except asyncio.CancelledError:
            # The request is already on its way, and the child the agent forks for it is nobody's until the reply says
            # which id it got. Let the call finish on its own and close whatever it produced.
            spawn_call.add_done_callback(self._close_orphan_spawn)
            raise

        process_id = ProcessId(obj.id)
        if process_id in self._processes or process_id in self._retired_ids:
            raise RuntimeError(f'Duplicate remote process id: {process_id!r}')

        spool_policy = options.get(SpoolPolicy, SpoolPolicy())
        storage = SpoolStorage(
            memory_cap=spool_policy.memory_cap,
            spill_dir=self._spill_dir if spool_policy.spill else None,
            spill_name=f'{process_id}.spool',
            keep_spill=spool_policy.keep_spill,
        )
        spool = OutputSpool(storage, AsyncioSpoolNotifier())
        self._spools.add(spool)

        process = RemoteProcess(
            manager=self,
            process_id=process_id,
            pid=obj.pid,
            spec=spec,
            options=options,
            scope=scope,
            created_at=obj.created_at,
            spool=spool,
        )

        if scope.closing:
            self._processes[process_id] = process
            for _, event in self._pending_events.pop(process_id, []):
                self._apply_event(process, event)
            await process.aclose()
            spool.close()
            raise ScopeClosedError('/'.join(scope.path))

        scope._register(process)  # noqa
        self._processes[process_id] = process

        # Announced before anything that got ahead of the spawn reply - a short-lived child's exit, typically - is
        # applied, so that its events follow.
        self._events.publish_soon(ProcessSpawnedEvent(
            process_id=process.id,
            pid=process.pid,
            scope_path=tuple(scope.path),
            argv=tuple(spec.argv),
            name=spec.name,
        ))
        for _, event in self._pending_events.pop(process_id, []):
            self._apply_event(process, event)
        await self._events.flush()
        return process

    ##
    # Events from the agent

    def _apply_event(self, process: RemoteProcess, event: ta.Any) -> None:
        if isinstance(event, RemoteProcessOutputEvent):
            process._on_output(event.fd, event.data)  # noqa
        elif isinstance(event, RemoteProcessOutputEndEvent):
            process._on_output_end()  # noqa
        elif isinstance(event, RemoteProcessExitedEvent):
            process._on_exited(event.returncode)  # noqa
        else:
            raise TypeError(event)

    def handle_event(self, method: str, params: ta.Any) -> None:
        """
        Applies a process event notification from the agent. Synchronous, and called from the peer's receive loop in
        wire order: an output chunk is in its spool before anything the agent sent after it - the reply to a
        `process.close` in particular - is seen.
        """

        if method == REMOTE_PROCESS_OUTPUT_METHOD:
            event: ta.Any = unmarshal_obj(params, RemoteProcessOutputEvent)
        elif method == REMOTE_PROCESS_OUTPUT_END_METHOD:
            event = unmarshal_obj(params, RemoteProcessOutputEndEvent)
        elif method == REMOTE_PROCESS_EXITED_METHOD:
            event = unmarshal_obj(params, RemoteProcessExitedEvent)
        else:
            raise ValueError(method)

        process_id = event.id
        if (process := self._processes.get(ProcessId(process_id))) is not None:
            self._apply_event(process, event)
        elif process_id not in self._retired_ids:
            # Ahead of its spawn's reply: kept for registration.
            self._pending_events.setdefault(process_id, []).append((method, event))

    def _on_peer_closed(self, peer: RpcPeer) -> None:
        self.connection_lost(peer.failure)

    def connection_lost(self, failure: BaseException | None) -> None:
        reason = f'RPC connection lost: {failure!r}' if failure is not None else 'RPC connection closed'
        for process in list(self._processes.values()):
            process._on_connection_lost(reason)  # noqa
        self._pending_events.clear()

    ##
    # Scope hooks

    def reparent(self, process: Process, new_scope: ProcessScope) -> None:
        remote_process = check.isinstance(process, RemoteProcess)
        old_scope = remote_process.scope
        old_scope._unregister(remote_process)  # noqa
        remote_process._set_scope(new_scope)  # noqa
        new_scope._register(remote_process)  # noqa
        self._publish_soon(ProcessReparentedEvent(
            process_id=remote_process.id,
            pid=remote_process.pid,
            scope_path=tuple(new_scope.path),
            old_scope_path=tuple(old_scope.path),
        ))

    def scope_opened(self, scope: ProcessScope) -> None:
        if self._state == 'new':
            return
        self._publish_soon(ScopeOpenedEvent(scope_path=tuple(scope.path)))

    async def scope_closed(
            self,
            scope: ProcessScope,
            result: ScopeCloseResult,
    ) -> None:
        await self._events.publish_now(ScopeClosedEvent(
            scope_path=tuple(scope.path),
            num_processes=result.num_processes,
            num_abandoned=result.num_abandoned,
        ))

    async def close_processes(
            self,
            process_list: ta.Sequence[Process],
            policy: ScopeClosePolicy,
    ) -> ScopeCloseResult:
        errors: list[Exception] = []

        async def close_one(process: Process) -> None:
            try:
                await process.aclose()
            except Exception as e:  # noqa
                errors.append(e)

        task = asyncio.gather(*[close_one(process) for process in process_list])
        try:
            await asyncio.wait_for(task, policy.overall_timeout_s)
        except TimeoutError:
            for process in process_list:
                if not process.state.is_terminal:
                    try:
                        await process.kill()
                    except Exception as e:  # noqa
                        errors.append(e)
        return ScopeCloseResult(num_processes=len(process_list), errors=errors)

    ##
    # Close

    async def aclose(self) -> None:
        if self._state == 'closed':
            return
        if self._state == 'new':
            self._state = 'closed'
            return
        self._state = 'closing'
        try:
            await self._root.aclose()

        except asyncio.CancelledError:
            # Out of time. A teardown still in flight could only be waiting on a reply from the agent, which may never
            # come: give up on it - its handle is poisoned - rather than hold the caller for it.
            for task in list(self._tasks):
                task.cancel()
            raise

        finally:
            while True:
                self._events.ensure_draining()
                await self._join_tasks()
                if not self._events.busy:
                    break

            any_spill_kept = False
            for spool in self._spools:
                if not spool.storage.closed:
                    spool.close()
                if spool.spill_path is not None:
                    any_spill_kept = True
            self._spools.clear()
            if self._own_spill_dir and self._spill_dir is not None and not any_spill_kept:
                shutil.rmtree(self._spill_dir, ignore_errors=True)
            self._state = 'closed'
