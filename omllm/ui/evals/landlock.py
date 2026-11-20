import ctypes
import os
import sys
import typing as ta

from omcore import dataclasses as dc

from .assets import eval_resources


##


@dc.dataclass(frozen=True)
class LocalReadAccess:
    trees: tuple[str, ...] = ()
    directories: tuple[str, ...] = ()
    files: tuple[str, ...] = ()


def restrict_local_access(write_paths: ta.Sequence[str], read_access: LocalReadAccess | None) -> None:
    """Apply inherited Linux Landlock filesystem restrictions before an untrusted command starts."""

    if sys.platform != 'linux':
        raise OSError('The local runtime requires Linux Landlock')

    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    libc.prctl.restype = ctypes.c_int

    def syscall(number: int, *args: ta.Any) -> int:
        result = libc.syscall(number, *args)
        if result < 0:
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        return result

    class RulesetAttr(ctypes.Structure):
        _fields_ = [('handled_access_fs', ctypes.c_uint64)]

    class PathBeneathAttr(ctypes.Structure):
        _fields_ = [('allowed_access', ctypes.c_uint64), ('parent_fd', ctypes.c_int32)]

    # WRITE_FILE, REMOVE_DIR/FILE, MAKE_*, REFER, and TRUNCATE (Landlock ABI 3).
    write_access = (1 << 1) | sum(1 << bit for bit in range(4, 15))
    read_file = 1 << 2
    read_dir = 1 << 3
    read_tree = read_file | read_dir
    handled_access = write_access | (read_tree if read_access is not None else 0)
    ruleset = syscall(444, ctypes.byref(RulesetAttr(handled_access)), ctypes.sizeof(RulesetAttr), 0)
    try:
        access_by_path: dict[str, int] = {}

        def add_path(path: str, access: int) -> None:
            access_by_path[path] = access_by_path.get(path, 0) | access

        for path in write_paths:
            add_path(path, write_access | (read_tree if read_access is not None else 0))
        add_path('/dev/null', (1 << 1) | (1 << 14) | (read_file if read_access is not None else 0))
        if read_access is not None:
            for path in read_access.trees:
                add_path(path, read_tree)
            for path in read_access.directories:
                add_path(path, read_dir)
            for path in read_access.files:
                add_path(path, read_file)

        for path, access in access_by_path.items():
            fd = os.open(path, os.O_PATH | os.O_CLOEXEC)
            try:
                if not os.path.isdir(path):
                    access &= (1 << 1) | (1 << 14) | read_file
                rule = PathBeneathAttr(access, fd)
                syscall(445, ruleset, 1, ctypes.byref(rule), 0)
            finally:
                os.close(fd)
        if libc.prctl(38, 1, 0, 0, 0):
            error = ctypes.get_errno()
            raise OSError(error, os.strerror(error))
        syscall(446, ruleset, 0)
    finally:
        os.close(ruleset)


def check_local_runtime() -> int:
    if sys.platform != 'linux':
        raise ValueError('The local runtime requires Linux Landlock')
    libc = ctypes.CDLL(None, use_errno=True)
    libc.syscall.restype = ctypes.c_long
    abi = libc.syscall(444, 0, 0, 1)
    if abi < 3:
        raise ValueError('The local runtime requires Landlock ABI 3 or newer')
    return abi


def local_environment(
        workdir: str,
        scratch: str,
        *,
        tests: str | None = None,
) -> dict[str, str]:
    env = {
        'HOME': scratch,
        'PATH': os.path.join(scratch, 'bin') + os.pathsep + '/usr/bin:/bin',
        'TMPDIR': scratch,
        'PYTHONDONTWRITEBYTECODE': '1',
        'PYTHONPATH': workdir,
        'MINIEVAL_WORKDIR': workdir,
        'MINIEVAL_PYTHON': sys.executable,
    }
    if tests is not None:
        env['MINIEVAL_TESTS_DIR'] = tests
    return env


def prepare_local_scratch(scratch: str) -> None:
    os.mkdir(scratch)
    bin_dir = os.path.join(scratch, 'bin')
    os.mkdir(bin_dir)
    for name in ('python', 'python3'):
        os.symlink(sys.executable, os.path.join(bin_dir, name))


def local_system_read_trees() -> tuple[str, ...]:
    return tuple(path for path in (
        os.path.join(sys.prefix, 'bin'),
        os.path.join(sys.prefix, 'lib'),
        os.path.join(sys.base_prefix, 'bin'),
        os.path.join(sys.base_prefix, 'lib'),
        '/usr/bin',
        '/usr/lib',
        '/usr/lib64',
        '/usr/share',
        '/usr/local/bin',
        '/usr/local/lib',
        '/etc/ssl/certs',
        '/etc/pki/tls/certs',
    ) if os.path.isdir(path))


def local_grader_read_access(tests: str) -> LocalReadAccess:
    return LocalReadAccess(
        trees=(*local_system_read_trees(), tests),
        files=tuple(path for path in (
            '/etc/ld.so.cache', '/dev/urandom', '/dev/random', os.path.join(sys.prefix, 'pyvenv.cfg'),
        ) if os.path.isfile(path)),
    )


def local_agent_read_access(
        *,
        blocked: str,
        files: ta.Sequence[str] = (),
        trees: ta.Sequence[str] = (),
) -> LocalReadAccess:
    resources = eval_resources()
    excluded = [os.path.realpath(blocked)]
    if isinstance(resources, os.PathLike):
        excluded.append(os.path.realpath(resources))

    read_dirs: list[str] = []
    read_trees: list[str] = []
    read_files: list[str] = list(files)

    def collect(path: str) -> None:
        path = os.path.realpath(path)
        if any(path == p or path.startswith(p + os.sep) for p in excluded):
            return
        if os.path.isdir(path):
            if any(p.startswith(path + os.sep) for p in excluded):
                read_dirs.append(path)
                for name in os.listdir(path):
                    collect(os.path.join(path, name))
            else:
                read_trees.append(path)
        elif os.path.isfile(path):
            read_files.append(path)

    for path in local_system_read_trees():
        collect(path)

    return LocalReadAccess(
        trees=(*read_trees, *trees),
        directories=tuple(read_dirs),
        files=(*read_files, *(path for path in (
            '/etc/hosts',
            '/etc/resolv.conf',
            '/etc/nsswitch.conf',
            '/etc/gai.conf',
            '/etc/passwd',
            '/etc/group',
            '/etc/ld.so.cache',
            os.path.join(sys.prefix, 'pyvenv.cfg'),
            '/dev/urandom',
            '/dev/random',
        ) if os.path.isfile(path))),
    )


def _main() -> None:
    # Runs before the tool server starts, with fresh stdio and without using a subprocess preexec hook.
    workdir, scratch, task_path, bootstrap = sys.argv[1:]
    environment = local_environment(workdir, scratch)
    os.chdir(workdir)
    restrict_local_access([workdir, scratch], local_agent_read_access(blocked=task_path))
    os.execve(sys.executable, [sys.executable, '-IS', '-c', bootstrap], environment)


if __name__ == '__main__':
    _main()
