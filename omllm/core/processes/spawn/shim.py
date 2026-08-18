# ruff: noqa: UP006 UP007 UP045
"""
The spawn shim: runs in the child, after fork and before exec, applying everything the parent asked for that
`subprocess.Popen` cannot do safely with threads (privilege drop, rlimits, deathsig, signal disposition cleanup), then
`execvpe`s the target. Failures at any stage are reported as a single marshal'd record over the status fd, which is
otherwise closed-on-exec so that EOF alone means "exec happened".

**Pure stdlib, zero om imports, py3.8-safe syntax.** The source is loaded as a resource and shipped to the child (or,
later, to a remote host) as text and exec'd in a bare namespace, so nothing here may depend on the om codebase or on a
modern interpreter. It is intentionally *not* marked `@om-lite` (that would subject it to a lite-import precheck, and it
lives under the non-lite `omllm.core` package which cannot be imported under 3.8) - but the same constraints apply: keep
it stdlib-only and syntactically valid back to Python 3.8. `# type:` comment annotations and the `UP*` noqa above exist
for exactly that reason.

The payload is a marshal-able dict; os-level strings are bytes:
  argv: [bytes], env: {bytes: bytes}, cwd: bytes|None, status_fd: int, keep_fds: [int], close_fds: [int], umask:
  int|None, rlimits: [(resource, soft, hard)], user: int|bytes|None, group: int|bytes|None, extra_groups:
  [int|bytes]|None, deathsig: int|None
"""
import marshal
import os
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


def _write_all(fd, data):  # type: (int, bytes) -> None
    view = memoryview(data)
    while view:
        n = os.write(fd, view)
        view = view[n:]


def report_error(status_fd, stage, exc):  # type: (int, str, BaseException) -> None
    errno = getattr(exc, 'errno', None)
    if not isinstance(errno, int):
        errno = None
    try:
        msg = str(exc) or repr(exc)
    except Exception:  # noqa
        msg = repr(exc)
    try:
        _write_all(status_fd, marshal.dumps((stage, errno, msg)))
    except Exception:  # noqa
        pass


##


def _resolve_gid(group):  # type: (ta.Any) -> int
    if isinstance(group, int):
        return group
    import grp  # noqa
    return grp.getgrnam(os.fsdecode(group)).gr_gid


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
            pw = pwd.getpwnam(os.fsdecode(user))
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
    for name in ('SIGPIPE', 'SIGXFSZ', 'SIGXFZ'):
        sig = getattr(_sig, name, None)
        if sig is not None:
            try:
                _sig.signal(sig, _sig.SIG_DFL)
            except (OSError, ValueError, RuntimeError):
                pass
    # exec also preserves the blocked mask, and Popen does not reset it.
    if hasattr(_sig, 'pthread_sigmask'):
        try:
            _sig.pthread_sigmask(_sig.SIG_SETMASK, ())
        except (OSError, ValueError):
            pass


def apply_fds(status_fd, keep_fds, close_fds):  # type: (int, ta.Any, ta.Any) -> None
    # `pass_fds` makes everything inheritable in the child - the status fd must NOT survive exec (its EOF is the success
    # signal), and internal fds must not leak into the target.
    for fd in close_fds or ():
        if fd == status_fd:
            continue
        try:
            os.close(fd)
        except OSError:
            pass
    for fd in keep_fds or ():
        os.set_inheritable(fd, True)
    os.set_inheritable(status_fd, False)


##


def set_controlling_tty():  # type: () -> None
    # fd 0 is the pty slave (Popen dup2'd it); the process is a session leader (start_new_session), so it has no
    # controlling terminal yet and this ioctl makes the slave its ctty. Must run in the child, before exec.
    import fcntl  # noqa
    import termios  # noqa
    fcntl.ioctl(0, termios.TIOCSCTTY, 0)


def main(payload):  # type: (ta.Any) -> None
    status_fd = payload['status_fd']
    stage = 'payload'
    try:
        argv = list(payload['argv'])
        env = dict(payload['env'])
        cwd = payload.get('cwd')

        stage = 'umask'
        umask = payload.get('umask')
        if umask is not None:
            os.umask(umask)

        stage = 'rlimit'
        apply_rlimits(payload.get('rlimits'))

        stage = 'credentials'
        apply_credentials(payload.get('user'), payload.get('group'), payload.get('extra_groups'))

        # After the credential change: the kernel clears the death signal on uid/gid changes.
        stage = 'deathsig'
        deathsig = payload.get('deathsig')
        if deathsig is not None:
            apply_deathsig(deathsig)

        stage = 'chdir'
        if cwd:
            os.chdir(cwd)

        stage = 'ctty'
        if payload.get('set_ctty'):
            set_controlling_tty()

        stage = 'fds'
        apply_fds(status_fd, payload.get('keep_fds'), payload.get('close_fds'))

        stage = 'signals'
        reset_signals()

        stage = 'exec'
        os.execvpe(argv[0], argv, env)

    except BaseException as e:  # noqa
        report_error(status_fd, stage, e)
        os._exit(EXIT_CODE)


def _main():  # type: () -> None
    """
    Debug entrypoint: `python -m omllm.core.processes.spawn.shim <payload_fd>` with a marshal'd payload on that fd.
    """

    fd = int(sys.argv[1])
    with os.fdopen(fd, 'rb') as f:
        payload = marshal.load(f)  # noqa: S302
    main(payload)


if __name__ == '__main__':
    _main()
