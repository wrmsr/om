# ruff: noqa: UP006 UP007 UP045
"""
The spawn shim: the first thing every child execs. It runs in the child, before the real exec, applying everything the
parent asked for that cannot (or should not) be done between fork and exec in the parent's address space - receiving
the passed fds and putting them where the target expects them, closing every other fd, privilege drop, umask, rlimits,
deathsig, signal disposition cleanup, chdir, controlling tty - then `execvpe`s the target. Failures at any stage are
reported as a single JSON record over the control socket, which is otherwise closed-on-exec so that EOF alone means
"exec happened".

**Pure stdlib, zero om imports, py3.8-safe syntax.** The source is loaded as a resource and shipped to the child (or,
later, to a remote host) as text and exec'd as a module, so nothing here may depend on the om codebase or on a modern
interpreter. It is intentionally *not* marked `@om-lite` (that would subject it to a lite-import precheck, and it
lives under the non-lite `omllm.core` package which cannot be imported under 3.8) - but the same constraints apply: keep
it stdlib-only and syntactically valid back to Python 3.8. `# type:` comment annotations and the `UP*` noqa above exist
for exactly that reason.

## Protocol

The child starts with exactly one thing from the parent: an AF_UNIX stream socket (the *control socket*) at the fd
number in `argv[1]`, delivered by a dup2 at spawn. Queued on it - sent by the parent before the child even runs - is a
header line `{"n": N}` followed by N fds via SCM_RIGHTS: first the *payload blob* (one line of json `ShimPayload`, then
this source), then the caller's pass-fds in `ShimPayload.keep_fds` order, which the shim dup2's onto the numbers listed
there. The bootstrap (`shim.py::BOOTSTRAP`) does the receive, reads the blob, execs the source as module
`__procs_shim__`, and calls `main(payload, passed_fds)`. On failure the shim writes `[stage, errno, message]` as json
to the control socket and exits 127; on success the socket closes at exec.

## Payload

`ShimPayload` is a plain dataclass whose fields are all json-able as they are (`dataclasses.asdict` one way,
`ShimPayload(**json.loads(...))` the other). The rest of the `processes` package imports this module to build one
(importing it runs nothing). OS strings that must round-trip *byte-exactly* - argv, env, cwd - travel as base64 of
their `os.fsencode`d bytes (`encode_os` / `decode_os`) and are handed to the OS as bytes here, so neither side's
filesystem encoding nor json's handling of odd code points can ever alter them. User / group *names* are plain str.
"""
import array
import base64
import dataclasses as dc
import json
import os
import socket
import sys
import typing as ta


if ta.TYPE_CHECKING:
    import signal as _sig
else:
    try:
        # The C accelerator: avoids the `signal` module's `enum` import in the hot spawn path.
        import _signal as _sig
    except ImportError:  # pragma: no cover
        import signal as _sig


##


EXIT_CODE = 127

PR_SET_PDEATHSIG = 1

# Per-message SCM_RIGHTS cap (Linux SCM_MAX_FD is 253) - the parent chunks, the bootstrap loops.
MAX_FDS_PER_MESSAGE = 200


def encode_os(s):  # type: (ta.Union[str, bytes]) -> str
    """An OS string (str via surrogate escapes, or bytes) as json-safe text: base64 of its bytes."""

    return base64.b64encode(os.fsencode(s) if isinstance(s, str) else s).decode('ascii')


def decode_os(s):  # type: (str) -> bytes
    return base64.b64decode(s)


@dc.dataclass(frozen=True)
class ShimPayload:
    """
    Everything the shim does, in the order it does it. Not kw-only (3.8). Field types are deliberately restricted to
    what round-trips through json unchanged: str, int, bool, None, and lists / dicts of those (tuples arrive as lists).
    """

    # The target: base64 OS strings (`encode_os`). `argv[0]` is resolved against `env`'s PATH (or `os.defpath`).
    argv: ta.List[str]

    # The target's exact environment: base64 OS strings for both keys and values.
    env: ta.Dict[str, str]

    # The control socket's fd: kept close-on-exec; an error record is written to it on failure.
    status_fd: int

    # Working directory for the target as a base64 OS string (None: unchanged).
    cwd: ta.Optional[str] = None

    # Close every fd >= 3 other than `status_fd` and `keep_fds` before exec. (Everything python opens is close-on-exec
    # anyway; this catches fds deliberately made inheritable by someone else.)
    close_fds: bool = True

    # The fd numbers at which the target expects the caller's passed fds - the ones received over the control socket
    # after the payload blob, in this order. They are dup2'd into place and made inheritable.
    keep_fds: ta.List[int] = dc.field(default_factory=list)

    # `os.umask` value (None: unchanged).
    umask: ta.Optional[int] = None

    # `(resource, soft, hard)` triples for `resource.setrlimit`.
    rlimits: ta.List[ta.List[int]] = dc.field(default_factory=list)

    # gosu-like privilege drop: uid or name, gid or name, supplementary gids or names. Names resolve in the child.
    user: ta.Union[int, str, None] = None
    group: ta.Union[int, str, None] = None
    extra_groups: ta.Optional[ta.List[ta.Union[int, str]]] = None

    # Linux: `PR_SET_PDEATHSIG` signal (None: none). Applied after the credential change, which would clear it.
    deathsig: ta.Optional[int] = None

    # Make fd 0 (a pty slave, dup2'd there by the parent) the controlling terminal.
    set_ctty: bool = False

    def to_json(self):  # type: () -> str
        return json.dumps(dc.asdict(self), separators=(',', ':'))

    @classmethod
    def from_json(cls, s):  # type: (ta.Union[str, bytes]) -> ShimPayload
        return cls(**json.loads(s))


##


def _write_all(fd, data):  # type: (int, bytes) -> None
    view = memoryview(data)
    while view:
        n = os.write(fd, view)
        view = view[n:]


def encode_error(stage, exc):  # type: (str, BaseException) -> bytes
    errno = getattr(exc, 'errno', None)
    if not isinstance(errno, int):
        errno = None
    try:
        msg = str(exc) or repr(exc)
    except Exception:  # noqa
        msg = repr(exc)
    return json.dumps([stage, errno, msg]).encode('utf-8')


def report_error(status_fd, stage, exc):  # type: (int, str, BaseException) -> None
    try:
        _write_all(status_fd, encode_error(stage, exc))
    except Exception:  # noqa
        pass


##


def receive_control(control_fd):  # type: (int) -> ta.Tuple[int, ta.List[int]]
    """
    Drains the control socket's queued handshake: returns `(payload_blob_fd, passed_fds)`. The socket object is
    detached again (the fd stays open and is the shim's status channel from here on). Mirrors the bootstrap exactly.
    """

    s = socket.socket(fileno=control_fd)
    try:
        buf = b''
        n = None  # type: ta.Optional[int]
        fds = array.array('i')
        while n is None or len(fds) < n:
            msg, anc, _flags, _addr = s.recvmsg(4096, socket.CMSG_SPACE(MAX_FDS_PER_MESSAGE * fds.itemsize))
            if not msg and not anc:
                raise EOFError('control socket closed during handshake')
            for level, typ, data in anc:
                if level == socket.SOL_SOCKET and typ == socket.SCM_RIGHTS:
                    fds.frombytes(data[:len(data) - (len(data) % fds.itemsize)])
            if n is None:
                buf += msg
                if b'\n' in buf:
                    n = int(json.loads(buf.split(b'\n', 1)[0])['n'])
    finally:
        s.detach()
    lst = list(fds)
    return lst[0], lst[1:]


##


def _resolve_gid(group):  # type: (ta.Union[int, str]) -> int
    if isinstance(group, int):
        return group
    import grp  # noqa
    return grp.getgrnam(group).gr_gid


def apply_credentials(user, group, extra_groups):  # type: (ta.Any, ta.Any, ta.Any) -> None
    """gosu order: supplementary groups, then gid, then uid. A numeric uid without a passwd entry is allowed."""

    if user is None and group is None and extra_groups is None:
        return

    uid = None
    gid = None
    pw = None
    if user is not None:
        import pwd  # noqa
        if isinstance(user, int):
            uid = user
            try:
                pw = pwd.getpwuid(user)
            except KeyError:
                pw = None
        else:
            pw = pwd.getpwnam(user)
            uid = pw.pw_uid

    if group is not None:
        gid = _resolve_gid(group)
    elif pw is not None:
        gid = pw.pw_gid

    if extra_groups is not None:
        os.setgroups([_resolve_gid(g) for g in extra_groups])
    elif pw is not None and gid is not None:
        os.initgroups(pw.pw_name, gid)
    elif uid is not None:
        os.setgroups([])

    if gid is not None:
        os.setgid(gid)
    if uid is not None:
        os.setuid(uid)


def apply_rlimits(rlimits):  # type: (ta.Any) -> None
    if not rlimits:
        return
    import resource  # noqa
    for res, soft, hard in rlimits:
        resource.setrlimit(res, (soft, hard))


def apply_deathsig(sig):  # type: (int) -> None
    if not getattr(sys, 'platform').startswith('linux'):  # mypy workaround
        return
    import ctypes  # noqa
    libc = ctypes.CDLL(None, use_errno=True)
    if libc.prctl(PR_SET_PDEATHSIG, sig, 0, 0, 0) != 0:
        e = ctypes.get_errno()
        raise OSError(e, os.strerror(e))
    # The parent thread may already be gone - the pact would then never fire.
    if os.getppid() == 1:
        os.kill(os.getpid(), sig)


def reset_signals():  # type: () -> None
    # Python ignores these at startup and exec preserves dispositions; give the target POSIX defaults. Handlers
    # (SIGINT etc) revert to default on exec by themselves.
    for name in ('SIGPIPE', 'SIGXFSZ'):
        sig = getattr(_sig, name, None)
        if sig is not None:
            try:
                _sig.signal(sig, _sig.SIG_DFL)
            except (OSError, ValueError, RuntimeError):
                pass
    # exec also preserves the blocked mask, and the spawner does not reset it.
    if hasattr(_sig, 'pthread_sigmask'):
        try:
            _sig.pthread_sigmask(_sig.SIG_SETMASK, ())
        except (OSError, ValueError):
            pass


def _open_fds():  # type: () -> ta.Optional[ta.List[int]]
    """The fds open in this process, or None if the platform offers no cheap way to list them."""

    for d in ('/proc/self/fd', '/dev/fd'):
        try:
            names = os.listdir(d)
        except OSError:
            continue
        out = []
        for n in names:
            try:
                out.append(int(n))
            except ValueError:
                pass
        return out
    return None


def close_other_fds(keep):  # type: (ta.Iterable[int]) -> None
    """Closes every fd >= 3 not in `keep`."""

    keep_set = set(keep)
    fds = _open_fds()
    if fds is not None:
        for fd in fds:
            if fd >= 3 and fd not in keep_set:
                try:
                    os.close(fd)
                except OSError:
                    pass
        return

    # No fd listing: close the gaps between kept fds (close_range on Linux 5.9+ / FreeBSD, a loop elsewhere).
    try:
        max_fd = os.sysconf('SC_OPEN_MAX')
    except (OSError, ValueError):
        max_fd = 1024
    lo = 3
    for fd in sorted(k for k in keep_set if k >= 3):
        if fd > lo:
            os.closerange(lo, fd)
        lo = fd + 1
    os.closerange(lo, max(max_fd, lo))


def place_passed_fds(received, wanted, status_fd):  # type: (ta.List[int], ta.List[int], int) -> None
    """
    Moves each received fd onto the number the target expects. The received numbers are arbitrary (the kernel picked
    them), so everything is first lifted above every number in play, then dup2'd into place - no ordering can clobber
    a not-yet-moved fd. The results are inheritable; the control socket must not be among the targets.
    """

    if len(received) != len(wanted):
        raise ValueError(f'received {len(received)} fds, expected {len(wanted)}')
    if not received:
        return
    if len(set(wanted)) != len(wanted):
        raise ValueError(f'duplicate pass-fd targets: {wanted!r}')
    for w in wanted:
        if w < 3 or w == status_fd:
            raise ValueError(f'invalid pass-fd target: {w}')

    import fcntl  # noqa
    floor = max([status_fd, *received, *wanted]) + 1
    lifted = []
    for fd in received:
        lifted.append(fcntl.fcntl(fd, fcntl.F_DUPFD_CLOEXEC, floor))
        os.close(fd)
    for fd, w in zip(lifted, wanted):
        os.dup2(fd, w)  # inheritable by default
        os.close(fd)


def apply_fds(status_fd, keep_fds, close_fds):  # type: (int, ta.Iterable[int], bool) -> None
    keep = list(keep_fds)
    if close_fds:
        close_other_fds([status_fd, *keep])
    # Passed fds must survive the exec; the control socket must NOT (its EOF is the success signal).
    for fd in keep:
        os.set_inheritable(fd, True)
    os.set_inheritable(status_fd, False)


##


def set_controlling_tty():  # type: () -> None
    # fd 0 is the pty slave (the spawner dup2'd it); the process is a session leader (setsid at spawn), so it has no
    # controlling terminal yet and this ioctl makes the slave its ctty. Must run in the child, before exec.
    import fcntl  # noqa
    import termios  # noqa
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)


def main(payload, passed_fds):  # type: (ShimPayload, ta.List[int]) -> None
    status_fd = payload.status_fd
    stage = 'payload'
    try:
        argv = [decode_os(a) for a in payload.argv]
        env = {decode_os(k): decode_os(v) for k, v in payload.env.items()}
        cwd = decode_os(payload.cwd) if payload.cwd is not None else None

        stage = 'pass_fds'
        place_passed_fds(list(passed_fds), list(payload.keep_fds), status_fd)

        stage = 'umask'
        if payload.umask is not None:
            os.umask(payload.umask)

        stage = 'rlimit'
        apply_rlimits(payload.rlimits)

        stage = 'credentials'
        apply_credentials(payload.user, payload.group, payload.extra_groups)

        # After the credential change: the kernel clears the death signal on uid/gid changes.
        stage = 'deathsig'
        if payload.deathsig is not None:
            apply_deathsig(payload.deathsig)

        stage = 'chdir'
        if cwd:
            os.chdir(cwd)

        stage = 'ctty'
        if payload.set_ctty:
            set_controlling_tty()

        stage = 'fds'
        apply_fds(status_fd, payload.keep_fds, payload.close_fds)

        stage = 'signals'
        reset_signals()

        stage = 'exec'
        os.execvpe(argv[0], argv, env)

    except BaseException as e:  # noqa
        report_error(status_fd, stage, e)
        os._exit(EXIT_CODE)


def _main():  # type: () -> None
    """
    Debug entrypoint: `python -m omllm.core.processes.launch._shim <control_fd>` with the handshake (header, blob fd,
    pass-fds) already queued on that socket, exactly as the bootstrap would see it. The blob's source part is ignored.
    """

    control_fd = int(sys.argv[1])
    blob_fd, passed = receive_control(control_fd)
    with os.fdopen(blob_fd, 'r', encoding='utf-8') as f:
        payload = ShimPayload.from_json(f.readline())
    main(payload, passed)


if __name__ == '__main__':
    _main()
