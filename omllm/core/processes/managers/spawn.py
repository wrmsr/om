"""
Forking the child: a small spawner over `os.posix_spawn` that returns nothing but the pid. There is deliberately no
`Popen` object anywhere in this package: `Popen` bundles a lifecycle (`__del__` reaps or parks the object in
`subprocess._active` for a later `Popen()` to reap, `send_signal` polls first, `__exit__` waits, ...) that is exactly
what the manager must own itself in order to keep a pid provably ours until it deliberately reaps it.

Division of labor with the spawn shim (`../launch/_shim.py`, the first thing every child execs): `posix_spawn` does
only what must happen between fork and exec - wire up 0/1/2, deliver the control socket, new session / process group,
default signal dispositions - and the shim, a full python process of our own, does everything else: receiving the
passed fds and putting them in place, closing every other fd, umask, rlimits, credentials, deathsig, chdir, controlling
tty, then the real exec.

No fd is ever made inheritable in this process. Stdio and the control socket reach the child through dup2 file
actions (a dup2 always yields a non-close-on-exec descriptor, and it happens in the child's own table); everything else
- the payload blob, the caller's pass-fds - is *sent* over the control socket with SCM_RIGHTS (`send_control_fds`),
queued before the child even runs: the kernel duplicates them straight into the child, and nothing about this process's
fd table changes. There is no window in which another thread's fork+exec could pick anything up.

INVARIANT: after `spawn_child` returns a pid, nothing here ever waits on it.
"""
import fcntl
import json
import os
import signal
import socket
import typing as ta

from omcore import check

from ..launch._shim import MAX_FDS_PER_MESSAGE


##


SessionMode: ta.TypeAlias = ta.Literal['session', 'group'] | None


# What `_Py_RestoreSignals()` resets at interpreter startup - the shim (being a python) re-ignores them, and resets them
# again itself before the real exec; this just keeps the shim's own run tidy (same as Popen's `restore_signals`).
_RESTORED_SIGNALS: ta.Final[ta.Sequence[int]] = tuple(
    s for s in (getattr(signal, n, None) for n in ('SIGPIPE', 'SIGXFSZ')) if s is not None
)


def _executable_candidates(executable: str, env: ta.Mapping[str, str] | None) -> list[str]:
    """Like execvpe: a path with a directory part is taken as is; else every PATH entry of `env` (or ours) is tried."""

    if os.path.dirname(executable):
        return [executable]
    return [os.path.join(d, executable) for d in os.get_exec_path(env)]


def make_control_socketpair() -> tuple[socket.socket, socket.socket]:
    """`(parent_end, child_end)`, both close-on-exec. The child end is delivered by `spawn_child(control=...)`."""

    return socket.socketpair(socket.AF_UNIX, socket.SOCK_STREAM)


def send_control_fds(sock: socket.socket, fds: ta.Sequence[int]) -> None:
    """
    Queues the handshake the shim (`_shim.receive_control` / the bootstrap) expects on the control socket: one line
    `{"n": N}` then the N fds via SCM_RIGHTS, chunked to the per-message cap. Safe to call before the child exists -
    the messages, fds included, wait in the socket.
    """

    header = (json.dumps({'n': len(fds)}) + '\n').encode('ascii')
    if not fds:
        sock.sendall(header)
        return
    first = True
    for i in range(0, len(fds), MAX_FDS_PER_MESSAGE):
        chunk = list(fds[i:i + MAX_FDS_PER_MESSAGE])
        socket.send_fds(sock, [header if first else b'+'], chunk)
        first = False


def spawn_child(
        argv: ta.Sequence[str],
        *,
        env: ta.Mapping[str, str] | None = None,
        stdin_fd: int = -1,
        stdout_fd: int = -1,
        stderr_fd: int = -1,
        control: tuple[int, int] | None = None,
        session_mode: SessionMode = None,
        restore_signals: bool = True,
) -> int:
    """
    Spawns `argv` (its `argv[0]` resolved against `env`'s PATH - or ours - when it has no directory part), returning the
    child's pid. `stdin_fd` / `stdout_fd` / `stderr_fd` become the child's 0/1/2 (-1 inherits ours); `control` is
    `(our_fd, child_fd)`: our fd is dup2'd to `child_fd` in the child. `env=None` inherits ours. An exec failure is
    raised here as the corresponding `OSError` (glibc >= 2.24, macOS and musl all report it properly); no child exists
    in that case.
    """

    argv = list(check.not_empty(argv))
    candidates = _executable_candidates(argv[0], env)
    env_map: ta.Mapping[str, str] = env if env is not None else os.environ

    file_actions: list[tuple] = []
    tmp_fds: list[int] = []
    try:
        moves: list[tuple[int, int]] = [
            (fd, t) for fd, t in ((stdin_fd, 0), (stdout_fd, 1), (stderr_fd, 2)) if fd != -1
        ]
        if control is not None:
            moves.append(control)
        targets = {t for _, t in moves}
        for fd, target in moves:
            if fd in targets:
                # A source that is also some move's target could be clobbered by an earlier dup2 (and dup2 onto itself
                # is not portably a CLOEXEC-clear) - lift it above every target first. The lifted copy is close-on-exec,
                # so it vanishes from the child by itself.
                fd = fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, max(targets) + 1)
                tmp_fds.append(fd)
            file_actions.append((os.POSIX_SPAWN_DUP2, fd, target))

        kwargs: dict[str, ta.Any] = {}
        if session_mode == 'session':
            kwargs['setsid'] = True
        elif session_mode == 'group':
            kwargs['setpgroup'] = 0
        elif session_mode is not None:
            raise ValueError(session_mode)
        if restore_signals:
            kwargs['setsigdef'] = list(_RESTORED_SIGNALS)

        last_exc: OSError | None = None
        for path in candidates:
            try:
                return os.posix_spawn(path, argv, env_map, file_actions=file_actions, **kwargs)
            except (FileNotFoundError, NotADirectoryError) as e:
                if last_exc is None:
                    last_exc = e
            except OSError as e:
                # EACCES etc: keep looking, but this is the error to report if nothing else works (as execvpe does).
                last_exc = e
        raise check.not_none(last_exc)

    finally:
        for fd in tmp_fds:
            try:
                os.close(fd)
            except OSError:
                pass
