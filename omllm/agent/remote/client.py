import asyncio
import os
import shutil
import signal
import tempfile
import types
import typing as ta

from omcore import check
from omcore.asyncs.asynclite import all as asl
from omcore.logs import all as logs

from ...core import processes
from ...core.processes.asyncio.notifier import AsyncioSpoolNotifier
from ...core.processes.handles import Process
from ...core.processes.managers.events import ProcessEventDrain
from ...core.processes.scopes.policies import ScopeClosePolicy
from ...core.processes.scopes.scope import ProcessScope
from ...core.processes.scopes.scope import ScopeCloseResult
from ...core.processes.scopes.scope import ScopeManager
from ...core.processes.spool.storage import SpoolStorage
from ...core.processes.types.events import ProcessEvent
from ...core.processes.types.options import ProcessOptions
from ...core.processes.types.options import TerminationPolicy
from ...core.processes.types.specs import ProcessSpec
from ...core.processes.types.specs import Stdio
from ...core.rpc.channels import RpcChannel
from ...core.rpc.errors import RpcConnectionClosedError
from ...core.rpc.errors import RpcRemoteError
from ...core.rpc.handlers import RpcHandler
from ...core.rpc.messages import RpcNotificationMessage
from ...core.rpc.peers import RpcPeer
from ..fs.ops import FsDirEntry
from ..fs.ops import FsFile
from ..fs.ops import FsFileChangedError
from ..fs.ops import FsGlobResult
from ..fs.ops import FsOps
from ..fs.ops import FsStat
from ..fs.ops import FsWriteResult
from .protocol import FS_GLOB_METHOD
from .protocol import FS_LIST_DIR_METHOD
from .protocol import FS_READ_FILE_METHOD
from .protocol import FS_RESOLVE_PATH_METHOD
from .protocol import FS_STAT_METHOD
from .protocol import FS_WRITE_FILE_METHOD
from .protocol import PROCESS_CLOSE_METHOD
from .protocol import PROCESS_EXITED_METHOD
from .protocol import PROCESS_OUTPUT_END_METHOD
from .protocol import PROCESS_OUTPUT_METHOD
from .protocol import PROCESS_RESIZE_METHOD
from .protocol import PROCESS_SIGNAL_METHOD
from .protocol import PROCESS_SPAWN_METHOD
from .protocol import PROCESS_WRITE_EOF_METHOD
from .protocol import PROCESS_WRITE_METHOD
from .protocol import check_remote_bool
from .protocol import check_remote_dict
from .protocol import check_remote_float
from .protocol import check_remote_int
from .protocol import check_remote_str
from .protocol import decode_remote_bytes
from .protocol import encode_remote_bytes


log = logs.get_module_logger(globals())


##


_REMOTE_BUILTIN_EXCEPTIONS: ta.Final[ta.Mapping[str, type[Exception]]] = {
    'builtins.FileExistsError': FileExistsError,
    'builtins.FileNotFoundError': FileNotFoundError,
    'builtins.IsADirectoryError': IsADirectoryError,
    'builtins.NotADirectoryError': NotADirectoryError,
    'builtins.PermissionError': PermissionError,
}


def _translate_remote_error(exc: RpcRemoteError) -> Exception:
    if exc.remote_type.endswith('._RemoteFsFileChangedError'):
        return FsFileChangedError(exc.remote_message)
    if (cls := _REMOTE_BUILTIN_EXCEPTIONS.get(exc.remote_type)) is not None:
        return cls(exc.remote_message)
    return exc


def _decode_fs_entry(value: ta.Any) -> FsDirEntry:
    obj = check_remote_dict(value, {'name', 'path', 'is_dir', 'is_file', 'is_symlink'})
    return FsDirEntry(
        name=check_remote_str(obj['name']),
        path=check_remote_str(obj['path']),
        is_dir=check_remote_bool(obj['is_dir']),
        is_file=check_remote_bool(obj['is_file']),
        is_symlink=check_remote_bool(obj['is_symlink']),
    )


class RemoteFsOps(FsOps):
    def __init__(self, peer: RpcPeer) -> None:
        super().__init__()

        self._peer = peer

    async def _call(self, method: str, params: ta.Any) -> ta.Any:
        try:
            return await self._peer.call(method, params)
        except RpcRemoteError as e:
            raise _translate_remote_error(e) from e

    async def resolve_path(self, path: str) -> str:
        return check_remote_str(await self._call(FS_RESOLVE_PATH_METHOD, {'path': path}))

    async def stat(self, path: str) -> FsStat:
        obj = check_remote_dict(
            await self._call(FS_STAT_METHOD, {'path': path}),
            {'path', 'size', 'is_dir', 'is_file', 'is_symlink'},
        )
        return FsStat(
            path=check_remote_str(obj['path']),
            size=check_remote_int(obj['size'], minimum=0),
            is_dir=check_remote_bool(obj['is_dir']),
            is_file=check_remote_bool(obj['is_file']),
            is_symlink=check_remote_bool(obj['is_symlink']),
        )

    async def read_file(self, path: str) -> FsFile:
        obj = check_remote_dict(await self._call(FS_READ_FILE_METHOD, {'path': path}), {'data', 'digest'})
        return FsFile(
            data=decode_remote_bytes(obj['data']),
            digest=check_remote_str(obj['digest'], non_empty=True),
        )

    async def write_file(
            self,
            path: str,
            content: bytes | bytearray | memoryview,
            *,
            overwrite: bool = False,
            expected_digest: str | None = None,
    ) -> FsWriteResult:
        obj = check_remote_dict(await self._call(FS_WRITE_FILE_METHOD, {
            'path': path,
            'content': encode_remote_bytes(bytes(content)),
            'overwrite': overwrite,
            'expected_digest': expected_digest,
        }), {'created'})
        return FsWriteResult(created=check_remote_bool(obj['created']))

    async def list_dir(self, path: str) -> ta.Sequence[FsDirEntry]:
        value = await self._call(FS_LIST_DIR_METHOD, {'path': path})
        if not isinstance(value, list):
            raise TypeError(f'Expected remote directory entry list, got {value!r}')
        return [_decode_fs_entry(entry) for entry in value]

    async def glob(
            self,
            pattern: str,
            *,
            root: str,
            max_results: int | None = None,
    ) -> FsGlobResult:
        obj = check_remote_dict(await self._call(FS_GLOB_METHOD, {
            'pattern': pattern,
            'root': root,
            'max_results': max_results,
        }), {'entries', 'has_more'})
        entries = obj['entries']
        if not isinstance(entries, list):
            raise TypeError(f'Expected remote glob entry list, got {entries!r}')
        return FsGlobResult(
            entries=[_decode_fs_entry(entry) for entry in entries],
            has_more=check_remote_bool(obj['has_more']),
        )


##


class RemoteProcess(processes.Process):
    def __init__(
            self,
            *,
            manager: 'RemoteProcessManager',  # noqa: UP037
            process_id: processes.ProcessId,
            pid: int,
            spec: processes.ProcessSpec,
            options: processes.ProcessOptions,
            scope: processes.ProcessScope,
            created_at: float,
            spool: processes.OutputSpool,
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

        self._state = processes.ProcessState.RUNNING
        self._returncode: int | None = None
        self._exited = asyncio.Event()
        self._output_ended = asyncio.Event()
        self._stdin_closed = not self.has_stdin
        self._close_task: asyncio.Task[None] | None = None

        if isinstance(spec.stdio, processes.PtyStdio):
            self._winsize: tuple[int, int] | None = (spec.stdio.rows, spec.stdio.cols)
        else:
            self._winsize = None

    @property
    def id(self) -> processes.ProcessId:
        return self._id

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def spec(self) -> processes.ProcessSpec:
        return self._spec

    @property
    def options(self) -> processes.ProcessOptions:
        return self._options

    @property
    def state(self) -> processes.ProcessState:
        return self._state

    @property
    def returncode(self) -> int | None:
        return self._returncode

    @property
    def scope(self) -> processes.ProcessScope:
        return self._scope

    def _set_scope(self, scope: processes.ProcessScope) -> None:
        self._scope = scope

    @property
    def created_at(self) -> float:
        return self._created_at

    @property
    def closing(self) -> bool:
        return self._close_task is not None and not self._close_task.done()

    @property
    def exited(self) -> bool:
        return self._exited.is_set() and self._state is not processes.ProcessState.POISONED

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
        self._state = processes.ProcessState.EXITED
        self._exited.set()
        self._manager._publish_soon(processes.ProcessExitedEvent(  # noqa
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
        self._state = processes.ProcessState.REAPED
        self._on_output_end()
        self._stdin_closed = True
        self._manager._process_finished(self)  # noqa: SLF001
        self._manager._publish_soon(processes.ProcessReapedEvent(  # noqa
            process_id=self._id,
            pid=self._pid,
            scope_path=tuple(self._scope.path),
            returncode=returncode,
        ))

    def _on_connection_lost(self, reason: str) -> None:
        if self._state.is_terminal:
            return
        self._state = processes.ProcessState.POISONED
        self._exited.set()
        self._on_output_end()
        self._stdin_closed = True
        self._manager._process_finished(self)  # noqa: SLF001
        self._manager._publish_soon(processes.ProcessPoisonedEvent(  # noqa
            process_id=self._id,
            pid=self._pid,
            scope_path=tuple(self._scope.path),
            reason=reason,
        ))

    async def wait(self, timeout: float | None = None) -> int:
        if not self._exited.is_set():
            if timeout is not None and timeout <= 0:
                raise processes.ProcessTimeoutError(f'{self!r} did not exit within {timeout}s')
            try:
                await asyncio.wait_for(self._exited.wait(), timeout)
            except TimeoutError:
                raise processes.ProcessTimeoutError(f'{self!r} did not exit within {timeout}s') from None
        if self._state is processes.ProcessState.POISONED:
            raise processes.ProcessPoisonedError(repr(self))
        return check.not_none(self._returncode)

    async def signal(self, sig: int, *, process_group: bool | None = None) -> None:
        if self._state.is_terminal:
            raise processes.ProcessNotAliveError(repr(self))
        if process_group is None:
            process_group = self._options.get(
                processes.TerminationPolicy,
                processes.TerminationPolicy(),
            ).process_group
        await self._manager._call(PROCESS_SIGNAL_METHOD, {  # noqa
            'id': self._id,
            'signal': sig,
            'process_group': process_group,
        })

    async def terminate(self) -> None:
        policy = self._options.get(processes.TerminationPolicy, processes.TerminationPolicy())
        await self.signal(policy.signal)

    async def kill(self) -> None:
        await self.signal(signal.SIGKILL)

    @property
    def has_stdin(self) -> bool:
        if isinstance(self._spec.stdio, processes.PtyStdio):
            return True
        return self._spec.stdio.stdin == 'pipe'

    @property
    def stdin_closed(self) -> bool:
        return self._stdin_closed

    async def write(self, data: bytes) -> None:
        if not self.has_stdin or self._stdin_closed:
            raise BrokenPipeError('process has no open stdin')
        await self._manager._call(PROCESS_WRITE_METHOD, {  # noqa
            'id': self._id,
            'data': encode_remote_bytes(data),
        })

    async def write_eof(self) -> None:
        if self._stdin_closed:
            return
        await self._manager._call(PROCESS_WRITE_EOF_METHOD, {'id': self._id})  # noqa
        self._stdin_closed = True

    @property
    def spool(self) -> processes.OutputSpool:
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
        return isinstance(self._spec.stdio, processes.PtyStdio)

    async def resize(self, rows: int, cols: int) -> None:
        if not self.has_pty:
            raise processes.NotAPtyError(repr(self))
        if self._state.is_terminal:
            raise processes.ProcessNotAliveError(repr(self))
        await self._manager._call(PROCESS_RESIZE_METHOD, {  # noqa
            'id': self._id,
            'rows': rows,
            'cols': cols,
        })
        self._winsize = (rows, cols)

    def get_winsize(self) -> tuple[int, int] | None:
        if self._state.is_terminal:
            return None
        return self._winsize

    async def aclose(
            self,
            policy: processes.TerminationPolicy | None = None,
            *,
            wait_s: float | None = None,
    ) -> None:
        if self._state.is_terminal:
            return
        if self._close_task is None:
            if policy is None:
                policy = self._options.get(processes.TerminationPolicy, processes.TerminationPolicy())
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
    processes.TerminationPolicy,
    processes.SpoolPolicy,
    processes.SessionMode,
    processes.RunTimeout,
    processes.Tag,
)

_REMOTE_PROCESS_EVENT_METHODS: ta.Final[ta.AbstractSet[str]] = frozenset([
    PROCESS_OUTPUT_METHOD,
    PROCESS_OUTPUT_END_METHOD,
    PROCESS_EXITED_METHOD,
])


class RemoteProcessManager(processes.ProcessManager, ScopeManager):
    def __init__(
            self,
            peer: RpcPeer,
            config: processes.ManagerConfig | None = None,
    ) -> None:
        super().__init__()

        self._peer = peer
        self._config = config if config is not None else processes.ManagerConfig()
        self._state: ta.Literal['new', 'started', 'closing', 'closed'] = 'new'
        self._processes: dict[processes.ProcessId, RemoteProcess] = {}
        self._pending_events: dict[str, list[tuple[str, ta.Any]]] = {}
        self._retired_ids: set[str] = set()
        self._tasks: set[asyncio.Task] = set()
        self._spools: set[processes.OutputSpool] = set()
        self._spill_dir: str | None = None
        self._own_spill_dir = False

        # Events are published strictly in the order they were raised, from one drain task at a time, whether they came
        # from a notification (exit, output end) or an async path.
        self._events = ProcessEventDrain(
            publish=self._publish,
            spawn_task=self._spawn_task,
            asynclite=asl.asyncio.All(),
        )

        self._root = processes.ProcessScope(
            'root',
            parent=None,
            manager=self,
            options=self._config.default_options,
            close_policy=self._config.close_policy,
        )

    @property
    def config(self) -> processes.ManagerConfig:
        return self._config

    @property
    def root(self) -> processes.ProcessScope:
        return self._root

    @property
    def processes(self) -> ta.Mapping[processes.ProcessId, processes.Process]:
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
            raise _translate_remote_error(e) from e

    @staticmethod
    def _encode_policy(policy: TerminationPolicy) -> ta.Mapping[str, ta.Any]:
        return {
            'signal': policy.signal,
            'grace_s': policy.grace_s,
            'kill_s': policy.kill_s,
            'close_stdin': policy.close_stdin,
            'process_group': policy.process_group,
            'drain_s': policy.drain_s,
        }

    def _process_finished(self, process: RemoteProcess) -> None:
        self._processes.pop(process.id, None)
        process.scope._unregister(process)  # noqa
        self._retired_ids.add(process.id)

    def _start_close(self, process: RemoteProcess, policy: TerminationPolicy) -> asyncio.Task[None]:
        async def run() -> None:
            try:
                obj = check_remote_dict(await self._call(PROCESS_CLOSE_METHOD, {
                    'id': process.id,
                    'policy': self._encode_policy(policy),
                }), {'returncode', 'state'})
                returncode = check_remote_int(obj['returncode'])
                if check_remote_str(obj['state']) != 'reaped':
                    raise RuntimeError(f'Unexpected remote process close state: {obj["state"]!r}')
                process._on_reaped(returncode)  # noqa
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
            obj = check_remote_dict(spawn_call.result(), {'id', 'pid', 'created_at', 'name'})
            process_id = check_remote_str(obj['id'], non_empty=True)
        except Exception:  # noqa
            return
        self._retired_ids.add(process_id)
        self._pending_events.pop(process_id, None)
        self._spawn_task(self._close_orphan(process_id))

    async def _close_orphan(self, process_id: str) -> None:
        try:
            await self._call(PROCESS_CLOSE_METHOD, {
                'id': process_id,
                'policy': self._encode_policy(TerminationPolicy()),
            })
        except RpcConnectionClosedError:
            # The agent tears down everything it still has when the connection goes.
            pass
        except Exception:  # noqa
            log.exception('Error closing orphaned remote process %r', process_id)

    @staticmethod
    def _encode_stdio(stdio: Stdio) -> ta.Mapping[str, ta.Any]:
        if isinstance(stdio, processes.PtyStdio):
            return {
                'kind': 'pty',
                'rows': stdio.rows,
                'cols': stdio.cols,
                'term': stdio.term,
            }

        for name, value in (
                ('stdin', stdio.stdin),
                ('stdout', stdio.stdout),
                ('stderr', stdio.stderr),
        ):
            if isinstance(value, int) or value == 'inherit':
                raise ValueError(f'Remote process stdio does not support {name}={value!r}')
        return {
            'kind': 'pipes',
            'stdin': stdio.stdin,
            'stdout': stdio.stdout,
            'stderr': stdio.stderr,
        }

    async def spawn(
            self,
            scope: ProcessScope,
            spec: ProcessSpec,
            options: ProcessOptions,
    ) -> Process:
        if self._state != 'started':
            if self.closed:
                raise processes.ManagerClosedError
            raise processes.ManagerNotStartedError
        unsupported = [option for option in options if not isinstance(option, _REMOTE_PROCESS_SUPPORTED_OPTIONS)]
        if unsupported:
            raise ValueError(f'Unsupported remote process options: {unsupported!r}')
        if (
                (session_mode := options.get(processes.SessionMode)) is not None and
                session_mode.mode != 'session'
        ):
            raise ValueError(f'Unsupported remote process session mode: {session_mode.mode!r}')

        spawn_call = asyncio.ensure_future(self._call(PROCESS_SPAWN_METHOD, {
            'argv': list(spec.argv),
            'cwd': spec.cwd,
            'env': dict(spec.env) if spec.env is not None else None,
            'stdio': self._encode_stdio(spec.stdio),
            'name': spec.name,
        }))
        try:
            obj = check_remote_dict(await asyncio.shield(spawn_call), {'id', 'pid', 'created_at', 'name'})
        except asyncio.CancelledError:
            # The request is already on its way, and the child the agent forks for it is nobody's until the reply says
            # which id it got. Let the call finish on its own and close whatever it produced.
            spawn_call.add_done_callback(self._close_orphan_spawn)
            raise

        process_id = processes.ProcessId(check_remote_str(obj['id'], non_empty=True))
        if process_id in self._processes or process_id in self._retired_ids:
            raise RuntimeError(f'Duplicate remote process id: {process_id!r}')

        spool_policy = options.get(processes.SpoolPolicy, processes.SpoolPolicy())
        storage = SpoolStorage(
            memory_cap=spool_policy.memory_cap,
            spill_dir=self._spill_dir if spool_policy.spill else None,
            spill_name=f'{process_id}.spool',
            keep_spill=spool_policy.keep_spill,
        )
        spool = processes.OutputSpool(storage, AsyncioSpoolNotifier())
        self._spools.add(spool)

        process = RemoteProcess(
            manager=self,
            process_id=process_id,
            pid=check_remote_int(obj['pid'], minimum=1),
            spec=spec,
            options=options,
            scope=scope,
            created_at=check_remote_float(obj['created_at'], minimum=0.),
            spool=spool,
        )

        if scope.closing:
            self._processes[process_id] = process
            for method, params in self._pending_events.pop(process_id, []):
                self._apply_event(process, method, params)
            await process.aclose()
            spool.close()
            raise processes.ScopeClosedError('/'.join(scope.path))

        scope._register(process)  # noqa
        self._processes[process_id] = process

        for method, params in self._pending_events.pop(process_id, []):
            self._apply_event(process, method, params)

        await self._events.publish_now(processes.ProcessSpawnedEvent(
            process_id=process.id,
            pid=process.pid,
            scope_path=tuple(scope.path),
            argv=tuple(spec.argv),
            name=spec.name,
        ))
        return process

    ##
    # Events from the agent

    def _apply_event(
            self,
            process: RemoteProcess,
            method: str,
            params: ta.Mapping[str, ta.Any],
    ) -> None:
        if method == PROCESS_OUTPUT_METHOD:
            process._on_output(  # noqa
                check_remote_int(params['fd'], minimum=1),
                decode_remote_bytes(params['data']),
            )
        elif method == PROCESS_OUTPUT_END_METHOD:
            process._on_output_end()  # noqa
        elif method == PROCESS_EXITED_METHOD:
            process._on_exited(check_remote_int(params['returncode']))  # noqa
        else:
            raise ValueError(method)

    def handle_event(self, method: str, params: ta.Any) -> None:
        """
        Applies a process event notification from the agent. Synchronous, and called from the peer's receive loop in
        wire order: an output chunk is in its spool before anything the agent sent after it - the reply to a
        `process.close` in particular - is seen.
        """

        if method == PROCESS_OUTPUT_METHOD:
            obj = check_remote_dict(params, {'id', 'fd', 'data'})
        elif method == PROCESS_OUTPUT_END_METHOD:
            obj = check_remote_dict(params, {'id'})
        elif method == PROCESS_EXITED_METHOD:
            obj = check_remote_dict(params, {'id', 'returncode'})
        else:
            raise ValueError(method)

        process_id = check_remote_str(obj['id'], non_empty=True)
        if (process := self._processes.get(processes.ProcessId(process_id))) is not None:
            self._apply_event(process, method, obj)
        elif process_id not in self._retired_ids:
            # Ahead of its spawn's reply: kept for registration.
            self._pending_events.setdefault(process_id, []).append((method, obj))

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
        self._publish_soon(processes.ProcessReparentedEvent(
            process_id=remote_process.id,
            pid=remote_process.pid,
            scope_path=tuple(new_scope.path),
            old_scope_path=tuple(old_scope.path),
        ))

    def scope_opened(self, scope: ProcessScope) -> None:
        if self._state == 'new':
            return
        self._publish_soon(processes.ScopeOpenedEvent(scope_path=tuple(scope.path)))

    async def scope_closed(
            self,
            scope: ProcessScope,
            result: ScopeCloseResult,
    ) -> None:
        await self._events.publish_now(processes.ScopeClosedEvent(
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


##


class _RemoteAgentClientHandler(RpcHandler):
    def __init__(self) -> None:
        super().__init__()

        self.processes: RemoteProcessManager | None = None

    def handle_notification_inline(self, method: str, params: ta.Any) -> bool:
        if method not in _REMOTE_PROCESS_EVENT_METHODS:
            return False
        if self.processes is None:
            raise RuntimeError('Remote process manager is not attached')
        self.processes.handle_event(method, params)
        return True

    async def handle(self, method: str, params: ta.Any) -> None:
        raise ValueError(f'Unexpected remote agent call: {method!r}')


class RemoteAgentClient:
    def __init__(
            self,
            channel: RpcChannel,
            *,
            process_config: processes.ManagerConfig | None = None,
    ) -> None:
        super().__init__()

        self._handler = _RemoteAgentClientHandler()
        self._peer = RpcPeer(
            channel,
            handler=self._handler,
            notification_error_handler=self._on_notification_error,
        )
        self._processes = RemoteProcessManager(self._peer, process_config)
        self._handler.processes = self._processes
        self._fs = RemoteFsOps(self._peer)

        self._peer.add_close_callback(self._on_peer_closed)
        self._started = False

    @property
    def peer(self) -> RpcPeer:
        return self._peer

    @property
    def fs(self) -> RemoteFsOps:
        return self._fs

    @property
    def processes(self) -> RemoteProcessManager:
        return self._processes

    def _on_notification_error(self, message: RpcNotificationMessage, error: BaseException) -> None:
        log.warning('Error handling remote agent event %r: %r', message.method, error)

    def _on_peer_closed(self, peer: RpcPeer) -> None:
        self._processes.connection_lost(peer.failure)

    async def start(self) -> None:
        if self._started:
            raise RuntimeError('Remote agent client has already been started')
        self._started = True
        await self._peer.start()
        try:
            await self._processes.start()
        except BaseException:
            await self._peer.aclose()
            raise

    async def wait_closed(self) -> None:
        await self._peer.wait_closed()

    async def aclose(self, *, timeout_s: float | None = None) -> None:
        """
        Closes the remote processes, then the connection. `timeout_s` bounds the graceful part: if the agent has not
        finished tearing its processes down by then - or is not answering at all - the connection is severed first,
        which fails every outstanding call and lets the process manager finish on its own.
        """

        if not self._started:
            await self._processes.aclose()
            await self._peer.aclose()
            return

        closing = asyncio.ensure_future(self._processes.aclose())
        try:
            done, _ = await asyncio.wait([closing], timeout=timeout_s)
        except BaseException:
            # Cancelled while waiting: sever the connection so the manager cannot wait on the agent any longer, and
            # still see it through.
            await self._peer.aclose()
            await asyncio.wait([closing])
            raise
        try:
            if not done:
                await self._peer.aclose()
            await closing
        finally:
            await self._peer.aclose()

    async def __aenter__(self) -> ta.Self:
        await self.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb) -> None:
        await self.aclose()
