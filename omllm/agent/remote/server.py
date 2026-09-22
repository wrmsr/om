# ruff: noqa: UP006 UP007 UP045
"""Python-3.8-compatible filesystem and process services used by the remote agent amalgam."""
import asyncio
import glob as glob_mod
import hashlib
import json
import os
import signal
import stat as stat_mod
import subprocess
import sys
import tempfile
import time
import typing as ta

from omcore.asyncs.asyncio.streams import asyncio_open_stream_reader
from omcore.asyncs.asyncio.streams import asyncio_open_stream_writer

from ...core.rpc.errors import RpcMethodNotFoundError
from ...core.rpc.handlers import RpcHandler
from ...core.rpc.peers import RpcPeer
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
from .protocol import check_remote_optional_int
from .protocol import check_remote_optional_str
from .protocol import check_remote_optional_str_dict
from .protocol import check_remote_str
from .protocol import check_remote_str_list
from .protocol import decode_remote_bytes
from .protocol import encode_remote_bytes


##


_REMOTE_PROCESS_OUTPUT_CHUNK_SIZE = 64 * 1024

_REMOTE_CLD_EXITED = getattr(os, 'CLD_EXITED', 1)
_REMOTE_CLD_KILLED = getattr(os, 'CLD_KILLED', 2)
_REMOTE_CLD_DUMPED = getattr(os, 'CLD_DUMPED', 3)

_REMOTE_PTY_CHILD_CODE = """
import fcntl
import json
import os
import sys
import termios

argv = json.loads(sys.argv[1])
os.setsid()
fcntl.ioctl(0, termios.TIOCSCTTY, 0)
os.execvpe(argv[0], argv, os.environ)
"""


def _remote_process_returncode(info: ta.Any) -> int:
    if info.si_code == _REMOTE_CLD_EXITED:
        return int(info.si_status)
    if info.si_code in (_REMOTE_CLD_KILLED, _REMOTE_CLD_DUMPED):
        return -int(info.si_status)
    raise RuntimeError(f'Unexpected waitid result: {info!r}')


def _remote_fs_digest(data: bytes) -> str:
    return hashlib.sha256(data).hexdigest()


def _remote_glob_root(pattern: str) -> str:
    if not os.path.isabs(pattern):
        raise ValueError(f'glob pattern must be absolute: {pattern!r}')

    pattern = os.path.normpath(pattern)
    drive, tail = os.path.splitdrive(pattern)
    root = drive + os.sep
    for part in tail.lstrip(os.sep).split(os.sep):
        if any(char in part for char in '*?['):
            break
        root = os.path.join(root, part)
    return root


def _remote_path_is_under(path: str, root: str) -> bool:
    try:
        return os.path.commonpath((path, root)) == root
    except ValueError:
        return False


class _RemoteFsFileChangedError(RuntimeError):
    pass


class _RemoteFsService:
    @staticmethod
    def _resolve(path: str) -> str:
        return os.path.abspath(os.path.realpath(path))

    @staticmethod
    def _entry(path: str, name: ta.Optional[str] = None) -> ta.Dict[str, ta.Any]:
        return {
            'name': os.path.basename(path) if name is None else name,
            'path': path,
            'is_dir': os.path.isdir(path),
            'is_file': os.path.isfile(path),
            'is_symlink': os.path.islink(path),
        }

    @staticmethod
    def _check_expected_digest(path: str, expected_digest: str) -> None:
        try:
            with open(path, 'rb') as f:  # noqa
                actual_digest = _remote_fs_digest(f.read())
        except FileNotFoundError:
            actual_digest = None

        if actual_digest != expected_digest:
            raise _RemoteFsFileChangedError(f'File changed since it was read: {path!r}')

    async def resolve_path(self, params: ta.Any) -> str:
        obj = check_remote_dict(params, {'path'})
        return self._resolve(check_remote_str(obj['path']))

    async def stat(self, params: ta.Any) -> ta.Dict[str, ta.Any]:
        obj = check_remote_dict(params, {'path'})
        path = check_remote_str(obj['path'])
        lst = os.lstat(path)
        st = os.stat(path)
        return {
            'path': path,
            'size': st.st_size,
            'is_dir': stat_mod.S_ISDIR(st.st_mode),
            'is_file': stat_mod.S_ISREG(st.st_mode),
            'is_symlink': stat_mod.S_ISLNK(lst.st_mode),
        }

    async def read_file(self, params: ta.Any) -> ta.Dict[str, ta.Any]:
        obj = check_remote_dict(params, {'path'})
        path = check_remote_str(obj['path'])
        with open(path, 'rb') as f:  # noqa
            data = f.read()
        return {
            'data': encode_remote_bytes(data),
            'digest': _remote_fs_digest(data),
        }

    async def write_file(self, params: ta.Any) -> ta.Dict[str, ta.Any]:
        obj = check_remote_dict(params, {'path', 'content', 'overwrite', 'expected_digest'})
        path = check_remote_str(obj['path'])
        content = decode_remote_bytes(obj['content'])
        overwrite = check_remote_bool(obj['overwrite'])
        expected_digest = check_remote_optional_str(obj['expected_digest'])

        dst_dir = os.path.dirname(path)
        tmp_dir = tempfile.mkdtemp(prefix='.omllm-write-', dir=dst_dir)
        tmp_path = os.path.join(tmp_dir, 'file')
        fd = -1
        try:
            fd = os.open(tmp_path, os.O_WRONLY | os.O_CREAT | os.O_EXCL, 0o666)
            with os.fdopen(fd, 'wb') as f:
                fd = -1
                f.write(content)

            try:
                lst = os.lstat(path)
            except FileNotFoundError:
                if expected_digest is not None:
                    raise _RemoteFsFileChangedError(f'File changed since it was read: {path!r}') from None
                os.link(tmp_path, path)
                os.unlink(tmp_path)
                tmp_path = ''
                return {'created': True}

            if not overwrite:
                raise FileExistsError(path)
            if not stat_mod.S_ISREG(lst.st_mode):
                raise IsADirectoryError(path)
            if expected_digest is not None:
                self._check_expected_digest(path, expected_digest)

            os.chmod(tmp_path, stat_mod.S_IMODE(lst.st_mode))
            os.replace(tmp_path, path)
            tmp_path = ''
            return {'created': False}

        finally:
            if fd >= 0:
                os.close(fd)
            if tmp_path:
                try:
                    os.unlink(tmp_path)
                except FileNotFoundError:
                    pass
            os.rmdir(tmp_dir)

    async def list_dir(self, params: ta.Any) -> ta.List[ta.Dict[str, ta.Any]]:
        obj = check_remote_dict(params, {'path'})
        path = check_remote_str(obj['path'])
        return [
            {
                'name': entry.name,
                'path': entry.path,
                'is_dir': entry.is_dir(),
                'is_file': entry.is_file(),
                'is_symlink': entry.is_symlink(),
            }
            for entry in os.scandir(path)
        ]

    async def glob(self, params: ta.Any) -> ta.Dict[str, ta.Any]:
        obj = check_remote_dict(params, {'pattern', 'root', 'max_results'})
        pattern = check_remote_str(obj['pattern'])
        root = check_remote_str(obj['root'])
        max_results = check_remote_optional_int(obj['max_results'], minimum=0)

        resolved_root = self._resolve(root)
        resolved_glob_root = self._resolve(_remote_glob_root(pattern))
        if not _remote_path_is_under(resolved_glob_root, resolved_root):
            raise ValueError(f'glob root {resolved_glob_root!r} is outside permitted root {resolved_root!r}')

        entries = []  # type: ta.List[ta.Dict[str, ta.Any]]
        has_more = False
        for path in glob_mod.iglob(pattern, recursive=True):
            if not _remote_path_is_under(self._resolve(path), resolved_root):
                continue
            if max_results is not None and len(entries) >= max_results:
                has_more = True
                break
            entries.append(self._entry(path))
        return {'entries': entries, 'has_more': has_more}


##


class _RemoteServerProcess:
    def __init__(
            self,
            service: '_RemoteProcessService',  # noqa: UP037
            process_id: str,
            popen: subprocess.Popen,
            *,
            created_at: float,
            pty_master_fd: ta.Optional[int],
            pty_winsize: ta.Optional[ta.Tuple[int, int]],
    ) -> None:
        super().__init__()

        self._service = service
        self.id = process_id
        self.popen = popen
        self.created_at = created_at

        self._pty_master_fd = pty_master_fd
        self._pty_winsize = pty_winsize

        self._stdin = None  # type: ta.Optional[asyncio.StreamWriter]
        self._read_transports = []  # type: ta.List[asyncio.BaseTransport]
        self._reader_tasks = []  # type: ta.List[asyncio.Task]
        self._output_task = None  # type: ta.Optional[asyncio.Task]
        self._wait_task = None  # type: ta.Optional[asyncio.Task]
        self._close_task = None  # type: ta.Optional[asyncio.Task]

        self._exited = asyncio.Event()
        self._output_ended = asyncio.Event()
        self._returncode = None  # type: ta.Optional[int]
        self._reaped = False

    @property
    def returncode(self) -> ta.Optional[int]:
        return self._returncode

    @property
    def exited(self) -> bool:
        return self._exited.is_set()

    async def _connect_reader(self, file: ta.IO, fd: int) -> None:
        reader = await asyncio_open_stream_reader(file)
        transport = reader._transport  # type: ignore[attr-defined]  # noqa
        if transport is not None:
            self._read_transports.append(transport)
        self._reader_tasks.append(asyncio.create_task(self._read_output(reader, fd)))

    async def start(self) -> None:
        if self._pty_master_fd is not None:
            read_file = os.fdopen(os.dup(self._pty_master_fd), 'rb', 0)
            write_file = os.fdopen(os.dup(self._pty_master_fd), 'wb', 0)
            await self._connect_reader(read_file, 1)
            self._stdin = await asyncio_open_stream_writer(write_file)
        else:
            if self.popen.stdout is not None:
                await self._connect_reader(self.popen.stdout, 1)
            if self.popen.stderr is not None:
                await self._connect_reader(self.popen.stderr, 2)
            if self.popen.stdin is not None:
                self._stdin = await asyncio_open_stream_writer(self.popen.stdin)

        self._output_task = asyncio.create_task(self._run_output(), name=f'remote-output-{self.id}')
        self._wait_task = asyncio.create_task(self._run_wait(), name=f'remote-wait-{self.id}')

    async def _read_output(self, reader: asyncio.StreamReader, fd: int) -> None:
        while True:
            try:
                data = await reader.read(_REMOTE_PROCESS_OUTPUT_CHUNK_SIZE)
            except OSError:
                # Linux pty masters report EIO when the slave closes; BSDs return EOF.
                return
            if not data:
                return
            await self._service.notify(PROCESS_OUTPUT_METHOD, {
                'id': self.id,
                'fd': fd,
                'data': encode_remote_bytes(data),
            })

    async def _run_output(self) -> None:
        try:
            if self._reader_tasks:
                await asyncio.gather(*self._reader_tasks)
        finally:
            self._output_ended.set()
            await self._service.notify(PROCESS_OUTPUT_END_METHOD, {'id': self.id})

    async def _run_wait(self) -> None:
        loop = asyncio.get_running_loop()
        try:
            info = await loop.run_in_executor(
                None,
                os.waitid,
                os.P_PID,
                self.popen.pid,
                os.WEXITED | os.WNOWAIT,
            )
            self._returncode = _remote_process_returncode(info)
        except BaseException:
            if self._reaped:
                return
            raise
        finally:
            if self._returncode is not None:
                self._exited.set()

        await self._service.notify(PROCESS_EXITED_METHOD, {
            'id': self.id,
            'returncode': self._returncode,
        })

    def _signal(self, sig: int, process_group: bool) -> None:
        if self._reaped:
            raise ProcessLookupError(self.popen.pid)
        if self.exited:
            # The unreaped leader keeps its pid, and therefore its process-group id, from being reused.
            if process_group:
                try:
                    os.killpg(self.popen.pid, sig)
                except ProcessLookupError:
                    pass
            return

        if process_group:
            # The pty bootstrap creates its session immediately after exec, but a signal can race that setup. Hitting
            # the owned pid as well ensures it cannot escape before its pgid exists.
            try:
                os.kill(self.popen.pid, sig)
            except ProcessLookupError:
                pass
            try:
                os.killpg(self.popen.pid, sig)
            except ProcessLookupError:
                pass
        else:
            os.kill(self.popen.pid, sig)

    async def signal(self, sig: int, process_group: bool) -> None:
        self._signal(sig, process_group)

    async def write(self, data: bytes) -> None:
        if self._stdin is None or self._stdin.is_closing():
            raise BrokenPipeError('process has no open stdin')
        self._stdin.write(data)
        await self._stdin.drain()

    async def write_eof(self) -> None:
        if self._stdin is None or self._stdin.is_closing():
            return
        try:
            self._stdin.write_eof()
        except (AttributeError, NotImplementedError):
            self._stdin.close()

    async def resize(self, rows: int, cols: int) -> None:
        if self._pty_master_fd is None:
            raise RuntimeError('process does not have a pty')
        import fcntl
        import struct
        import termios
        fcntl.ioctl(self._pty_master_fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))
        self._pty_winsize = (rows, cols)
        if not self.exited:
            try:
                os.killpg(self.popen.pid, signal.SIGWINCH)
            except ProcessLookupError:
                pass

    async def _wait_exited(self, timeout: ta.Optional[float]) -> bool:
        if self.exited:
            return True
        if timeout is not None and timeout <= 0:
            return False
        try:
            await asyncio.wait_for(asyncio.shield(self._exited.wait()), timeout)
        except asyncio.TimeoutError:  # noqa: UP041  # Python 3.8 compatibility.
            return self.exited
        return True

    async def _wait_output_ended(self, timeout: ta.Optional[float]) -> bool:
        if self._output_ended.is_set():
            return True
        if timeout is not None and timeout <= 0:
            return False
        try:
            await asyncio.wait_for(asyncio.shield(self._output_ended.wait()), timeout)
        except asyncio.TimeoutError:  # noqa: UP041  # Python 3.8 compatibility.
            return self._output_ended.is_set()
        return True

    def _close_streams(self) -> None:
        if self._stdin is not None:
            self._stdin.close()
        for transport in self._read_transports:
            transport.close()
        self._read_transports.clear()
        if self._pty_master_fd is not None:
            try:
                os.close(self._pty_master_fd)
            except OSError:
                pass
            self._pty_master_fd = None

    def _reap(self) -> None:
        if self._reaped:
            return
        _, status = os.waitpid(self.popen.pid, 0)
        self._reaped = True
        if self._returncode is None:
            self._returncode = os.waitstatus_to_exitcode(status)
            self._exited.set()
        self.popen.returncode = self._returncode

    async def _run_close(self, policy: ta.Mapping[str, ta.Any]) -> ta.Dict[str, ta.Any]:
        close_stdin = check_remote_bool(policy['close_stdin'])
        first_signal = check_remote_int(policy['signal'], minimum=1)
        grace_s = check_remote_float(policy['grace_s'], minimum=0.)
        kill_s = check_remote_float(policy['kill_s'], minimum=0.)
        process_group = check_remote_bool(policy['process_group'])
        drain_s = check_remote_float(policy['drain_s'], minimum=0.)

        if not self.exited:
            if close_stdin:
                try:
                    await self.write_eof()
                except Exception:  # noqa
                    pass
            self._signal(first_signal, process_group)
            if not await self._wait_exited(grace_s):
                self._signal(signal.SIGKILL, process_group)
                if not await self._wait_exited(kill_s):
                    self._close_streams()
                    raise RuntimeError(f'process {self.id!r} survived SIGKILL for {kill_s}s')

        # Sweep descendants while the unreaped leader still makes its process-group id safe to address.
        if process_group:
            self._signal(first_signal, True)
        if not self._output_ended.is_set():
            await self._wait_output_ended(drain_s)
        if process_group:
            self._signal(signal.SIGKILL, True)

        self._close_streams()
        if self._output_task is not None:
            await asyncio.gather(self._output_task, return_exceptions=True)
        self._reap()
        self._service.finished(self)
        return {'returncode': self._returncode, 'state': 'reaped'}

    async def close(self, policy: ta.Mapping[str, ta.Any]) -> ta.Dict[str, ta.Any]:
        if self._reaped:
            return {'returncode': self._returncode, 'state': 'reaped'}
        if self._close_task is None:
            self._close_task = asyncio.create_task(self._run_close(policy), name=f'remote-close-{self.id}')
        return await asyncio.shield(self._close_task)


class _RemoteProcessService:
    _DEFAULT_CLOSE_POLICY: ta.ClassVar[ta.Mapping[str, ta.Any]] = {
        'signal': int(signal.SIGTERM),
        'grace_s': 5.,
        'kill_s': 5.,
        'close_stdin': True,
        'process_group': True,
        'drain_s': 1.,
    }

    def __init__(self) -> None:
        super().__init__()

        self._peer = None  # type: ta.Optional[RpcPeer]
        self._processes = {}  # type: ta.Dict[str, _RemoteServerProcess]
        self._next_id = 1
        self._closed = False

    def set_peer(self, peer: RpcPeer) -> None:
        if self._peer is not None:
            raise RuntimeError('peer already set')
        self._peer = peer

    async def notify(self, method: str, params: ta.Any) -> None:
        if self._peer is None or self._peer.closed:
            return
        try:
            # Events are calls rather than fire-and-forget notifications. The acknowledgement makes process.close's
            # response an ordering barrier: by the time the host sees it, every preceding output chunk is in its spool.
            await self._peer.call(method, params)
        except Exception:  # noqa
            # The peer owns the connection failure. Keep draining child pipes until server teardown reaches us.
            pass

    def _lookup(self, process_id: ta.Any) -> _RemoteServerProcess:
        process_id = check_remote_str(process_id, non_empty=True)
        try:
            return self._processes[process_id]
        except KeyError:
            raise ValueError(f'No such remote process: {process_id!r}') from None

    def finished(self, process: _RemoteServerProcess) -> None:
        if self._processes.get(process.id) is process:
            self._processes.pop(process.id, None)

    @staticmethod
    def _stdio_value(value: str, *, stderr: bool = False) -> ta.Any:
        if value == 'pipe':
            return subprocess.PIPE
        if value == 'devnull':
            return subprocess.DEVNULL
        if stderr and value == 'stdout':
            return subprocess.STDOUT
        raise ValueError(f'Unsupported remote stdio channel: {value!r}')

    @staticmethod
    def _set_pty_winsize(fd: int, rows: int, cols: int) -> None:
        import fcntl
        import struct
        import termios
        fcntl.ioctl(fd, termios.TIOCSWINSZ, struct.pack('HHHH', rows, cols, 0, 0))

    async def spawn(self, params: ta.Any) -> ta.Dict[str, ta.Any]:
        if self._closed:
            raise RuntimeError('remote process service is closed')
        obj = check_remote_dict(params, {'argv', 'cwd', 'env', 'stdio', 'name'})
        argv = check_remote_str_list(obj['argv'], non_empty=True)
        cwd = check_remote_optional_str(obj['cwd'])
        env = check_remote_optional_str_dict(obj['env'])
        name = check_remote_optional_str(obj['name'])
        stdio = check_remote_dict(obj['stdio'], {'kind'}, {'stdin', 'stdout', 'stderr', 'rows', 'cols', 'term'})
        kind = check_remote_str(stdio['kind'])

        process_id = f'p{self._next_id}'
        self._next_id += 1

        master = None  # type: ta.Optional[int]
        slave = None  # type: ta.Optional[int]
        pty_winsize = None  # type: ta.Optional[ta.Tuple[int, int]]
        try:
            try:
                if kind == 'pipes':
                    stdin = self._stdio_value(check_remote_str(stdio['stdin']))
                    stdout = self._stdio_value(check_remote_str(stdio['stdout']))
                    stderr = self._stdio_value(check_remote_str(stdio['stderr']), stderr=True)
                    popen = subprocess.Popen(  # noqa: ASYNC220
                        argv,
                        cwd=cwd,
                        env=env,
                        stdin=stdin,
                        stdout=stdout,
                        stderr=stderr,
                        bufsize=0,
                        start_new_session=True,
                    )

                elif kind == 'pty':
                    rows = check_remote_int(stdio['rows'], minimum=1)
                    cols = check_remote_int(stdio['cols'], minimum=1)
                    term = check_remote_optional_str(stdio['term'])
                    if term is not None and (env is None or 'TERM' not in env):
                        env = dict(os.environ if env is None else env)
                        env['TERM'] = term

                    master, slave = os.openpty()
                    self._set_pty_winsize(slave, rows, cols)
                    pty_winsize = (rows, cols)
                    popen = subprocess.Popen(  # noqa: ASYNC220
                        [sys.executable, '-c', _REMOTE_PTY_CHILD_CODE, json.dumps(argv)],
                        cwd=cwd,
                        env=env,
                        stdin=slave,
                        stdout=slave,
                        stderr=slave,
                        close_fds=True,
                    )

                else:
                    raise ValueError(f'Invalid remote stdio kind: {kind!r}')

            except BaseException:
                if master is not None:
                    os.close(master)
                raise

        finally:
            if slave is not None:
                os.close(slave)

        process = _RemoteServerProcess(
            self,
            process_id,
            popen,
            created_at=time.time(),
            pty_master_fd=master,
            pty_winsize=pty_winsize,
        )
        try:
            await process.start()
            self._processes[process_id] = process
        except BaseException:
            try:
                os.kill(popen.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
            os.waitpid(popen.pid, 0)  # noqa: ASYNC222
            popen.returncode = -signal.SIGKILL
            if master is not None:
                try:
                    os.close(master)
                except OSError:
                    pass
            raise

        return {
            'id': process.id,
            'pid': process.popen.pid,
            'created_at': process.created_at,
            'name': name,
        }

    async def signal(self, params: ta.Any) -> None:
        obj = check_remote_dict(params, {'id', 'signal', 'process_group'})
        await self._lookup(obj['id']).signal(
            check_remote_int(obj['signal'], minimum=1),
            check_remote_bool(obj['process_group']),
        )

    async def close(self, params: ta.Any) -> ta.Dict[str, ta.Any]:
        obj = check_remote_dict(params, {'id', 'policy'})
        policy = check_remote_dict(
            obj['policy'],
            {'signal', 'grace_s', 'kill_s', 'close_stdin', 'process_group', 'drain_s'},
        )
        return await self._lookup(obj['id']).close(policy)

    async def write(self, params: ta.Any) -> None:
        obj = check_remote_dict(params, {'id', 'data'})
        await self._lookup(obj['id']).write(decode_remote_bytes(obj['data']))

    async def write_eof(self, params: ta.Any) -> None:
        obj = check_remote_dict(params, {'id'})
        await self._lookup(obj['id']).write_eof()

    async def resize(self, params: ta.Any) -> None:
        obj = check_remote_dict(params, {'id', 'rows', 'cols'})
        await self._lookup(obj['id']).resize(
            check_remote_int(obj['rows'], minimum=1),
            check_remote_int(obj['cols'], minimum=1),
        )

    async def aclose(self) -> None:
        if self._closed:
            return
        self._closed = True
        if self._processes:
            await asyncio.gather(*[
                process.close(self._DEFAULT_CLOSE_POLICY)
                for process in list(self._processes.values())
            ], return_exceptions=True)


##


class RemoteAgentRpcHandler(RpcHandler):
    def __init__(self) -> None:
        super().__init__()

        self._fs = _RemoteFsService()
        self._processes = _RemoteProcessService()
        self._methods = {
            FS_RESOLVE_PATH_METHOD: self._fs.resolve_path,
            FS_STAT_METHOD: self._fs.stat,
            FS_READ_FILE_METHOD: self._fs.read_file,
            FS_WRITE_FILE_METHOD: self._fs.write_file,
            FS_LIST_DIR_METHOD: self._fs.list_dir,
            FS_GLOB_METHOD: self._fs.glob,
            PROCESS_SPAWN_METHOD: self._processes.spawn,
            PROCESS_SIGNAL_METHOD: self._processes.signal,
            PROCESS_CLOSE_METHOD: self._processes.close,
            PROCESS_WRITE_METHOD: self._processes.write,
            PROCESS_WRITE_EOF_METHOD: self._processes.write_eof,
            PROCESS_RESIZE_METHOD: self._processes.resize,
        }

    def set_peer(self, peer: RpcPeer) -> None:
        self._processes.set_peer(peer)

    async def handle(self, method: str, params: ta.Any) -> ta.Any:
        try:
            fn = self._methods[method]
        except KeyError:
            raise RpcMethodNotFoundError(method) from None
        return await fn(params)

    async def aclose(self) -> None:
        await self._processes.aclose()
