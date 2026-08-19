"""
Forking the child: a small POSIX-only spawner over `_posixsubprocess.fork_exec` - the very primitive `subprocess.Popen`
is built on - that returns nothing but the pid. There is deliberately no `Popen` object anywhere in this package:
`Popen` bundles a lifecycle (`__del__` reaps or parks the object in `subprocess._active` for a later `Popen()` to reap,
`send_signal` polls first, `__exit__` waits, ...) that is exactly what the manager must own itself in order to keep a
pid provably ours until it deliberately reaps it. What we need from it - argument marshalling, the exec-failure error
pipe, `close_fds` / `pass_fds`, session/group creation, signal restoration - is a hundred lines, reproduced here.

INVARIANT: after `fork_exec` returns a pid, nothing here ever waits on it. The only `waitpid` below is for a child whose
own exec failed (reported over the error pipe): it is dead, never observed by anyone else, and reaped on the spot.

Requires CPython 3.14 (`_posixsubprocess.fork_exec`'s signature is version-specific; the codebase pins 3.14+).
"""
import _posixsubprocess  # noqa: PLC2701
import builtins
import os
import typing as ta

from omcore import check


##


ERRPIPE_MAX_READ: ta.Final[int] = 50_000

SessionMode: ta.TypeAlias = ta.Literal['session', 'group'] | None


def _errpipe_write_above_stdio(errpipe_write: int) -> int:
    """The child's error pipe must not sit in the 0-2 range, where the stdio dup2's would clobber it."""

    low: list[int] = []
    while errpipe_write < 3:
        low.append(errpipe_write)
        errpipe_write = os.dup(errpipe_write)
    for fd in low:
        os.close(fd)
    return errpipe_write


def _raise_child_error(errpipe_data: bytes, *, executable: bytes, cwd: str | None) -> ta.NoReturn:
    # Format written by _posixsubprocess: "ExceptionName:hex errno:description".
    try:
        exception_name, hex_errno, err_msg = errpipe_data.split(b':', 2)
        msg = err_msg.decode()
    except ValueError:
        raise RuntimeError(f'Bad exception data from child: {errpipe_data!r}') from None

    et = getattr(builtins, exception_name.decode('ascii', 'replace'), None)
    if isinstance(et, type) and issubclass(et, OSError) and hex_errno:
        errno_num = int(hex_errno, 16)
        filename: str | bytes | None
        if msg == 'noexec:chdir':
            msg, filename = '', cwd
        elif msg == 'noexec':
            msg, filename = '', None
        else:
            filename = executable
        if errno_num != 0:
            msg = os.strerror(errno_num)
        if filename is not None:
            raise et(errno_num, msg, filename)
        raise et(errno_num, msg)

    raise RuntimeError(msg)


def fork_exec(
        argv: ta.Sequence[str | bytes],
        *,
        env: ta.Mapping[str, str] | None = None,
        cwd: str | None = None,
        stdin_fd: int = -1,
        stdout_fd: int = -1,
        stderr_fd: int = -1,
        pass_fds: ta.Iterable[int] = (),
        session_mode: SessionMode = None,
        restore_signals: bool = True,
) -> int:
    """
    Forks and execs `argv[0]` (resolved against `env`'s PATH - or ours - when it has no directory part), returning the
    child's pid. `stdin_fd` / `stdout_fd` / `stderr_fd` are dup2'd onto 0/1/2 in the child (-1 inherits ours);
    every other fd is closed there except `pass_fds` (which are made inheritable). `env=None` inherits ours. An exec
    (or chdir) failure in the child is raised here as the corresponding `OSError`; the failed child is reaped.
    """

    args = [os.fsencode(a) for a in check.not_empty(argv)]
    executable = args[0]
    if os.path.dirname(executable):
        executable_list: tuple[bytes, ...] = (executable,)
    else:
        executable_list = tuple(os.path.join(os.fsencode(d), executable) for d in os.get_exec_path(env))

    env_list: list[bytes] | None
    if env is not None:
        env_list = []
        for k, v in env.items():
            kb = os.fsencode(k)
            if b'=' in kb:
                raise ValueError(f'Illegal environment variable name: {k!r}')
            env_list.append(kb + b'=' + os.fsencode(v))
    else:
        env_list = None

    if session_mode == 'session':
        call_setsid, pgid_to_set = True, -1
    elif session_mode == 'group':
        call_setsid, pgid_to_set = False, 0
    elif session_mode is None:
        call_setsid, pgid_to_set = False, -1
    else:
        raise ValueError(session_mode)

    errpipe_read, errpipe_write = os.pipe()
    try:
        try:
            errpipe_write = _errpipe_write_above_stdio(errpipe_write)
            fds_to_keep = {int(fd) for fd in pass_fds}
            fds_to_keep.add(errpipe_write)

            pid = _posixsubprocess.fork_exec(
                args,
                executable_list,
                True,  # close_fds
                tuple(sorted(fds_to_keep)),
                cwd,  # type: ignore[arg-type]  # str, bytes or None all fine (typeshed says str)
                env_list,
                stdin_fd,  # p2cread
                -1,  # p2cwrite
                -1,  # c2pread
                stdout_fd,  # c2pwrite
                -1,  # errread
                stderr_fd,  # errwrite
                errpipe_read,
                errpipe_write,
                restore_signals,
                call_setsid,
                pgid_to_set,
                None,  # gid
                None,  # extra_groups
                None,  # uid
                -1,  # umask
                None,  # type: ignore[arg-type]  # preexec_fn (typeshed says non-optional)
            )
        finally:
            os.close(errpipe_write)

        # Exec either happened (EOF, the pipe end was close-on-exec) or failed (an error record).
        errpipe_data = bytearray()
        while True:
            part = os.read(errpipe_read, ERRPIPE_MAX_READ)
            errpipe_data += part
            if not part or len(errpipe_data) > ERRPIPE_MAX_READ:
                break
    finally:
        os.close(errpipe_read)

    if errpipe_data:
        # The child never exec'd: it is dead (or dying) and provably nobody else's - reap it right here.
        try:
            os.waitpid(pid, 0)
        except ChildProcessError:
            pass
        _raise_child_error(bytes(errpipe_data), executable=executable, cwd=cwd)

    return pid
