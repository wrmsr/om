"""
Forking the child: a small spawner over `os.posix_spawn` that returns nothing but the pid. There is deliberately no
`Popen` object anywhere in this package: `Popen` bundles a lifecycle (`__del__` reaps or parks the object in
`subprocess._active` for a later `Popen()` to reap, `send_signal` polls first, `__exit__` waits, ...) that is exactly
what the manager must own itself in order to keep a pid provably ours until it deliberately reaps it.

Division of labor with the spawn shim (`../spawn/shim.py`, the first thing every child execs): `posix_spawn` does only
what must happen between fork and exec - wire up 0/1/2, new session / process group, default signal dispositions - and
the shim, a full python process of our own, does everything else: closing every fd but the ones meant to be passed,
umask, rlimits, credentials, deathsig, chdir, controlling tty, then the real exec. Because every fd python opens is
close-on-exec (PEP 446), a stray fd can at most reach the shim, never the target.

`pass_fds` are made inheritable in *this* process for the duration of the spawn (and restored afterwards): a
concurrent fork+exec from another thread that does not close its fds could see them. That is the same exposure the
launcher has always had for its payload fd, and nothing in-repo spawns that way.

INVARIANT: after `spawn_child` returns a pid, nothing here ever waits on it.
"""
import fcntl
import os
import signal
import typing as ta

from omcore import check


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


def spawn_child(
        argv: ta.Sequence[str],
        *,
        env: ta.Mapping[str, str] | None = None,
        stdin_fd: int = -1,
        stdout_fd: int = -1,
        stderr_fd: int = -1,
        pass_fds: ta.Iterable[int] = (),
        session_mode: SessionMode = None,
        restore_signals: bool = True,
) -> int:
    """
    Spawns `argv` (its `argv[0]` resolved against `env`'s PATH - or ours - when it has no directory part), returning the
    child's pid. `stdin_fd` / `stdout_fd` / `stderr_fd` become the child's 0/1/2 (-1 inherits ours); `pass_fds` are
    inherited; `env=None` inherits ours. An exec failure is raised here as the corresponding `OSError` (glibc >= 2.24,
    macOS and musl all report it properly); no child exists in that case.
    """

    argv = list(check.not_empty(argv))
    candidates = _executable_candidates(argv[0], env)
    env_map: ta.Mapping[str, str] = env if env is not None else os.environ

    file_actions: list[tuple] = []
    tmp_fds: list[int] = []
    flipped: list[tuple[int, bool]] = []
    try:
        for fd, target in ((stdin_fd, 0), (stdout_fd, 1), (stderr_fd, 2)):
            if fd == -1:
                continue
            if fd < 3:
                # A source in the 0-2 range could be clobbered by an earlier dup2 - lift it first. The lifted copy is
                # close-on-exec, so it vanishes from the child by itself.
                fd = fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, 3)
                tmp_fds.append(fd)
            file_actions.append((os.POSIX_SPAWN_DUP2, fd, target))

        for fd in pass_fds:
            was = os.get_inheritable(fd)
            if not was:
                os.set_inheritable(fd, True)
            flipped.append((fd, was))

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
        for fd, was in flipped:
            if not was:
                try:
                    os.set_inheritable(fd, False)
                except OSError:
                    pass
        for fd in tmp_fds:
            try:
                os.close(fd)
            except OSError:
                pass
