"""
Inject host bind mounts into running Docker containers without target-side tools.

Host: Python 3.10+, Docker CLI, macOS or Linux.
Daemon: rootful Linux Docker / Docker Desktop; Linux >= 5.12; amd64 or arm64.
Helpers: a native Linux image with Python 3.10+ (default: python:3.14-slim).

    python hotmount.py mount TARGET SOURCE /absolute/destination
    python hotmount.py unmount TARGET /absolute/destination
    python hotmount.py list

A nonprivileged donor stays running to retain the Docker-managed host share. Disposable privileged helpers perform
namespace operations. State lives in donor labels and its writable layer, not in a local host registry. Nothing is
executed in the target.

Mounts and destination placeholders are not persistent Docker configuration. Restarting or recreating the target does
not reinject them. Do not restart the target/donor, or run concurrent operations on overlapping destinations, while an
operation is in progress.

Destination symlinks, shared destination parents, userns-remapped targets, rootless Docker, and nonstandard runtimes
such as gVisor are deliberately outside this utility's scope. This is an administrative tool, not a hostile-container
security boundary.
"""
import argparse
import csv
import dataclasses as dc
import hashlib
import inspect
import io
import json
import os
import posixpath
import subprocess
import sys
import textwrap
import typing as ta
import uuid


##


_LABEL = 'io.wrmsr.hotmount.record'
_DEFAULT_IMAGE = 'python:3.14-slim'


@dc.dataclass(frozen=True)
class MountSpec:
    target_id: str
    target_name: str
    target_started: str
    source: str
    destination: str
    read_only: bool = False
    recursive: bool = False


def normalize_destination(destination: str) -> str:
    if not destination.startswith('/') or '\x00' in destination or '..' in destination.split('/'):
        raise ValueError('destination must be absolute and contain neither NUL nor .. components')
    destination = '/' + posixpath.normpath(destination).lstrip('/')
    if destination == '/':
        raise ValueError('refusing to mount over /')
    return destination


def build_donor_name(*, target_id: str, destination: str) -> str:
    digest = hashlib.sha256(f'{target_id}\0{destination}'.encode()).hexdigest()[:24]
    return f'hotmount-{digest}'


def build_bind_mount(spec: MountSpec) -> str:
    fields = [
        'type=bind',
        f'src={spec.source}',
        'dst=/hotmount-source',
        'bind-propagation=rprivate',
    ]
    if spec.read_only:
        fields.append('readonly')
    buf = io.StringIO()
    csv.writer(buf, lineterminator='', quoting=csv.QUOTE_ALL).writerow(fields)
    return buf.getvalue()


## Remote payload: all dependencies intentionally live inside this function.


def _do_ctypes_stuff() -> None:
    import contextlib
    import ctypes as ct
    import errno
    import fcntl
    import json
    import os
    import platform
    import stat
    import sys
    import typing as ta

    request = json.loads(sys.argv[1])
    if (
            sys.platform != 'linux' or
            platform.machine() not in ('x86_64', 'aarch64') or
            ct.sizeof(ct.c_void_p) != 8
    ):
        raise RuntimeError('helper must be native 64-bit Linux amd64/arm64')

    # Linux UAPI numbers shared by these two ABIs; never guess for other architectures.
    sys_open_tree = 428
    sys_move_mount = 429
    sys_mount_setattr = 442
    at_empty_path = 0x1000
    at_recursive = 0x8000
    open_tree_clone = 1
    clone_newns = 0x00020000
    clone_fs = 0x00000200
    ms_private = 1 << 18
    mount_attr_rdonly = 1
    move_mount_empty_paths = 0x04 | 0x40
    umount_nofollow = 8
    mnt_detach = 2

    libc = ct.CDLL(None, use_errno=True)
    libc.syscall.restype = ct.c_long
    libc.syscall.argtypes = [ct.c_long]  # Remaining arguments are variadic and explicitly typed below.
    libc.unshare.restype = ct.c_int
    libc.unshare.argtypes = [ct.c_int]
    libc.setns.restype = ct.c_int
    libc.setns.argtypes = [ct.c_int, ct.c_int]
    libc.umount2.restype = ct.c_int
    libc.umount2.argtypes = [ct.c_char_p, ct.c_int]

    class MountAttr(ct.Structure):
        _fields_ = [
            ('attr_set', ct.c_uint64),
            ('attr_clr', ct.c_uint64),
            ('propagation', ct.c_uint64),
            ('userns_fd', ct.c_uint64),
        ]

    def check(result: int, operation: str) -> int:
        if result == -1:
            err = ct.get_errno()

            hint = ''

            if err == errno.ENOSYS:
                hint = '; this utility requires Linux >= 5.12'
            elif err == errno.EPERM:
                hint = '; check rootful Docker, privileges, namespaces, and LSM policy'
            elif err == errno.EBUSY:
                hint = '; close users of the mount or use unmount --lazy (also needed for a mounted subtree)'

            raise OSError(err, f'{operation}: {os.strerror(err)}{hint}')

        return result

    def syscall(number: int, operation: str, *args: ta.Any) -> int:
        return check(libc.syscall(ct.c_long(number), *args), operation)

    @contextlib.contextmanager
    def opened(fd: int) -> ta.Iterator[int]:
        try:
            yield fd
        finally:
            os.close(fd)

    def read_text(path: str, *, dir_fd: int | None = None) -> str:
        fd = os.open(
            path,
            os.O_RDONLY | os.O_CLOEXEC,
            dir_fd=dir_fd,
        )
        with os.fdopen(fd, 'r') as f:
            return f.read()

    def read_mount_id(fd: int) -> int:
        for line in read_text(f'/proc/self/fdinfo/{fd}').splitlines():
            if line.startswith('mnt_id:'):
                return int(line.split(':', 1)[1])
        raise RuntimeError('mnt_id missing from proc fdinfo')

    def read_mounts(proc_fd: int) -> dict[int, list[str]]:
        return {
            int(parts[0]): parts
            for line in read_text('mountinfo', dir_fd=proc_fd).splitlines()
            if (parts := line.split())
        }

    def read_identity(proc_fd: int) -> dict[str, ta.Any]:
        ns = os.stat('ns/mnt', dir_fd=proc_fd)
        fields = read_text('stat', dir_fd=proc_fd).rsplit(')', 1)[1].split()

        return {
            'boot_id': read_text('/proc/sys/kernel/random/boot_id').strip(),
            'start_ticks': int(fields[19]),  # /proc/PID/stat field 22; comm may contain spaces or ')'.
            'mnt_ns': [ns.st_dev, ns.st_ino],
        }

    def open_process(pid: int, stack: contextlib.ExitStack) -> int:
        if pid <= 0:
            raise ValueError('invalid container PID')

        proc_fd = stack.enter_context(opened(os.open(  # noqa
            f'/proc/{pid}',
            os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC,
        )))

        ours = os.stat('/proc/self/ns/user')
        theirs = os.stat('ns/user', dir_fd=proc_fd)

        if (ours.st_dev, ours.st_ino) != (theirs.st_dev, theirs.st_ino):
            raise RuntimeError('userns-remapped containers are not supported')

        return proc_fd

    def check_identity(proc_fd: int, expected: dict[str, ta.Any]) -> None:
        if read_identity(proc_fd) != expected:
            raise RuntimeError('container process or mount namespace changed; refusing to continue')

    def enter_namespace(fd: int) -> None:
        # Native/background threads can share fs_struct even without Python threading objects.
        check(libc.unshare(clone_fs), 'unshare(CLONE_FS)')
        check(libc.setns(fd, clone_newns), 'setns(mount)')

    def open_parent(
            root_fd: int,
            destination: str,
            *,
            create: bool,
            stack: contextlib.ExitStack,
    ) -> tuple[int, str]:
        parts = destination.split('/')[1:]
        if not parts or any(not p or p in ('.', '..') for p in parts):
            raise ValueError('destination must be a normalized absolute path other than /')

        current = root_fd
        for part in parts[:-1]:
            try:
                fd = os.open(
                    part,
                    os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                    dir_fd=current,
                )

            except FileNotFoundError:
                if not create:
                    raise

                try:
                    os.mkdir(part, 0o755, dir_fd=current)
                except FileExistsError:
                    pass

                fd = os.open(
                    part,
                    os.O_PATH | os.O_DIRECTORY | os.O_NOFOLLOW | os.O_CLOEXEC,
                    dir_fd=current,
                )

            current = stack.enter_context(opened(fd))

        return current, parts[-1]

    def open_destination(parent_fd: int, name: str, *, create_mode: int | None = None) -> int:
        try:
            fd = os.open(
                name, os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=parent_fd,
            )

        except FileNotFoundError:
            if create_mode is None:
                raise

            try:
                if stat.S_ISDIR(create_mode):
                    os.mkdir(name, 0o755, dir_fd=parent_fd)
                else:
                    os.close(os.open(
                        name, os.O_WRONLY | os.O_CREAT | os.O_EXCL | os.O_NOFOLLOW | os.O_CLOEXEC,
                        0o644,
                        dir_fd=parent_fd,
                    ))

            except FileExistsError:
                pass

            fd = os.open(
                name,
                os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=parent_fd,
            )

        mode = os.fstat(fd).st_mode

        if not (stat.S_ISDIR(mode) or stat.S_ISREG(mode)):
            os.close(fd)
            raise ValueError('destination must be a real directory or regular file, not a symlink/special file')

        if create_mode is not None and stat.S_ISDIR(mode) != stat.S_ISDIR(create_mode):
            os.close(fd)
            raise ValueError('source and destination have different file/directory types')

        return fd

    def save_receipt(root_fd: int, receipt: dict[str, ta.Any]) -> None:
        fd = os.open(
            '.hotmount-receipt.tmp',
            os.O_WRONLY | os.O_CREAT | os.O_TRUNC | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=root_fd,
        )

        with os.fdopen(fd, 'w') as f:
            json.dump(receipt, f)
            f.flush()
            os.fsync(f.fileno())

        os.replace(
            '.hotmount-receipt.tmp', '.hotmount-receipt.json',
            src_dir_fd=root_fd,
            dst_dir_fd=root_fd,
        )

    with contextlib.ExitStack() as stack:
        donor_proc_fd = open_process(request['donor_pid'], stack)
        target_proc_fd = open_process(request['target_pid'], stack)

        identities = {
            'donor': read_identity(donor_proc_fd),
            'target': read_identity(target_proc_fd),
        }

        if request['operation'] == 'probe':
            print(json.dumps(identities))
            return

        if identities != request['identities']:
            raise RuntimeError('container changed since probe; refusing stale PID/namespace')

        donor_root_fd = stack.enter_context(opened(os.open(  # noqa
            'root',
            os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC,
            dir_fd=donor_proc_fd,
        )))

        target_root_fd = stack.enter_context(opened(os.open(  # noqa
            'root',
            os.O_PATH | os.O_DIRECTORY | os.O_CLOEXEC,
            dir_fd=target_proc_fd,
        )))

        donor_ns_fd = stack.enter_context(opened(os.open(  # noqa
            'ns/mnt',
            os.O_RDONLY | os.O_CLOEXEC,
            dir_fd=donor_proc_fd,
        )))

        target_ns_fd = stack.enter_context(opened(os.open(  # noqa
            'ns/mnt',
            os.O_RDONLY | os.O_CLOEXEC,
            dir_fd=target_proc_fd,
        )))

        check_identity(donor_proc_fd, identities['donor'])
        check_identity(target_proc_fd, identities['target'])

        lock_fd = stack.enter_context(opened(os.open(  # noqa
            '.hotmount.lock',
            os.O_RDWR | os.O_CREAT | os.O_NOFOLLOW | os.O_CLOEXEC,
            0o600,
            dir_fd=donor_root_fd,
        )))

        fcntl.flock(lock_fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        try:
            receipt = json.loads(read_text('.hotmount-receipt.json', dir_fd=donor_root_fd))
        except FileNotFoundError:
            receipt = None

        destination = request['destination']

        if request['operation'] == 'mount':
            if receipt is not None:
                raise RuntimeError('donor already has a receipt; unmount/clean up before retrying')

            source_fd = stack.enter_context(opened(os.open(  # noqa
                'hotmount-source',
                os.O_PATH | os.O_NOFOLLOW | os.O_CLOEXEC,
                dir_fd=donor_root_fd,
            )))

            source_mode = os.fstat(source_fd).st_mode
            if not (stat.S_ISDIR(source_mode) or stat.S_ISREG(source_mode)):
                raise ValueError('only directories and regular files are supported')

            parent_fd, name = open_parent(
                target_root_fd,
                destination,
                create=True,
                stack=stack,
            )

            dest_fd = stack.enter_context(opened(open_destination(  # noqa
                parent_fd,
                name, create_mode=source_mode,
            )))

            if read_mount_id(dest_fd) != read_mount_id(parent_fd):
                raise RuntimeError('destination is already a mountpoint; refusing to stack mounts')

            mounts = read_mounts(target_proc_fd)
            parent = mounts[read_mount_id(parent_fd)]
            if any(p.startswith('shared:') for p in parent[6:parent.index('-')]):
                raise RuntimeError('destination parent mount is shared; refusing propagation outside the target')

            # Cloning requires the source to belong to the caller's current mount namespace.

            enter_namespace(donor_ns_fd)

            tree_flags = at_empty_path | open_tree_clone | os.O_CLOEXEC
            if request['recursive']:
                tree_flags |= at_recursive

            mount_fd = stack.enter_context(opened(syscall(  # noqa
                sys_open_tree,
                'open_tree',
                ct.c_int(source_fd),
                ct.c_char_p(b''),
                ct.c_uint(tree_flags),
            )))

            attrs = MountAttr(
                attr_set=mount_attr_rdonly if request['read_only'] else 0,
                propagation=ms_private,
            )

            syscall(
                sys_mount_setattr,
                'mount_setattr',
                ct.c_int(mount_fd),
                ct.c_char_p(b''),
                ct.c_uint(at_empty_path | at_recursive),
                ct.byref(attrs),
                ct.c_size_t(ct.sizeof(attrs)),
            )

            receipt = {
                'target_identity': identities['target'],
                'destination': destination,
                'mount_id': read_mount_id(mount_fd),
                'status': 'prepared',
            }

            # Record the mount ID BEFORE attachment: an interrupted client can still reverse it.

            save_receipt(donor_root_fd, receipt)
            check_identity(target_proc_fd, identities['target'])
            enter_namespace(target_ns_fd)

            syscall(
                sys_move_mount,
                'move_mount',
                ct.c_int(mount_fd),
                ct.c_char_p(b''),
                ct.c_int(dest_fd),
                ct.c_char_p(b''),
                ct.c_uint(move_mount_empty_paths),
            )

            receipt['status'] = 'mounted'
            save_receipt(donor_root_fd, receipt)

            print(json.dumps(receipt))

            return

        if request['operation'] != 'unmount':
            raise ValueError(f"unknown operation: {request['operation']}")

        if receipt is None:
            print(json.dumps({'status': 'never-attached'}))
            return

        if (
                receipt['target_identity'] != identities['target'] or
                receipt['destination'] != destination
        ):
            raise RuntimeError('receipt belongs to a different target incarnation/destination; refusing to unmount')

        mounts = read_mounts(target_proc_fd)
        mount_id = receipt['mount_id']
        if mount_id not in mounts:
            print(json.dumps({'status': 'already-detached'}))
            return

        parent_fd, name = open_parent(
            target_root_fd,
            destination,
            create=False,
            stack=stack,
        )

        with opened(open_destination(parent_fd, name)) as dest_fd:  # noqa
            if read_mount_id(dest_fd) != mount_id:
                raise RuntimeError('destination no longer exposes our mount; refusing to unmount a replacement')

            entry = mounts[mount_id]
            if any(p.startswith('shared:') for p in entry[6:entry.index('-')]):
                raise RuntimeError('injected mount was made shared; refusing a potentially propagating unmount')

        # Do not retain an FD/cwd on the injected mount: that would make a normal umount EBUSY.
        check_identity(target_proc_fd, identities['target'])
        enter_namespace(target_ns_fd)

        flags = umount_nofollow | (mnt_detach if request['lazy'] else 0)
        path = os.fsencode(f'/proc/self/fd/{parent_fd}/{name}')
        check(libc.umount2(path, flags), 'umount2')

        receipt['status'] = 'detached'
        save_receipt(donor_root_fd, receipt)

        print(json.dumps(receipt))


## Host-side Docker orchestration.


class DockerCli:
    def __init__(
            self,
            *,
            executable: str = 'docker',
            context: str | None = None,
            timeout: float = 300.,
            verbose: bool = False,
    ) -> None:
        super().__init__()

        self._prefix = [executable]
        if context is not None:
            self._prefix.extend(['--context', context])

        self._timeout = timeout
        self._verbose = verbose

    def run(self, *args: str) -> str:
        if self._verbose:
            # Do not flood stderr with the several-hundred-line Python payload.
            shown = list(args)
            if '-c' in shown:
                index = shown.index('-c')
                shown[index + 1] = '<python payload>'
            print(f'docker {shown!r}', file=sys.stderr)

        try:
            result = subprocess.run(
                [
                    *self._prefix,
                    *args,
                ],
                stdin=subprocess.DEVNULL,
                stdout=subprocess.PIPE,
                stderr=subprocess.PIPE,
                text=True,
                timeout=self._timeout,
            )

        except subprocess.TimeoutExpired as exc:
            raise RuntimeError(f'docker {args[0]} timed out after {self._timeout:g} seconds') from exc

        if result.returncode:
            raise RuntimeError(f'docker {args[0]} failed ({result.returncode}):\n{result.stderr.strip()}')

        return result.stdout.strip()

    def inspect(self, container: str) -> dict[str, ta.Any]:
        return json.loads(self.run('container', 'inspect', container))[0]


def require_running(info: ta.Mapping[str, ta.Any]) -> None:
    if (
            not info['State']['Running'] or
            info['State']['Pid'] <= 0 or
            info['State'].get('Restarting')
    ):
        raise RuntimeError(f"container is not stably running: {info['Name']}")


def require_same_incarnation(before: ta.Mapping[str, ta.Any], after: ta.Mapping[str, ta.Any]) -> None:
    require_running(after)
    for key in ('Pid', 'StartedAt'):
        if before['State'][key] != after['State'][key]:
            raise RuntimeError(f"container restarted during operation: {after['Name']}")


class HotMounter:
    def __init__(
            self,
            docker: DockerCli,
            *,
            image: str = _DEFAULT_IMAGE,
            python: str = 'python3',
    ) -> None:
        super().__init__()

        self._docker = docker
        self._image = image
        self._python = python

    def _get_platform(self) -> str:
        info = json.loads(self._docker.run('info', '--format', '{{json .}}'))

        if info.get('OSType') != 'linux':
            raise RuntimeError('the Docker daemon must run Linux containers')

        if any('rootless' in s for s in info.get('SecurityOptions', [])):
            raise RuntimeError('rootless Docker is not supported')

        arch = {
            'x86_64': 'amd64',
            'amd64': 'amd64',
            'aarch64': 'arm64',
            'arm64': 'arm64',
        }.get(info['Architecture'])

        if arch is None:
            raise RuntimeError(f"unsupported daemon architecture: {info['Architecture']}")

        return f'linux/{arch}'

    def _remote(self, request: ta.Mapping[str, ta.Any], *, platform: str) -> dict[str, ta.Any]:
        source = textwrap.dedent(inspect.getsource(_do_ctypes_stuff)) + '\n_do_ctypes_stuff()\n'
        name = f'hotmount-helper-{uuid.uuid4().hex}'

        completed = False

        try:
            output = self._docker.run(
                'run',
                '--rm',
                '--name',
                name,
                '--platform',
                platform,
                '--privileged',
                '--pid=host',
                '--userns=host',
                '--user=0:0',
                '--network=none',
                '--entrypoint',
                self._python,
                self._image,
                '-I',
                '-S',
                '-c',
                source,
                json.dumps(request),
            )

            completed = True  # --rm handles a completed run, even if JSON decoding fails below.

            return json.loads(output)

        finally:
            # Killing a timed-out Docker CLI does not necessarily kill its container.

            if not completed:
                try:
                    self._docker.run('container', 'rm', '--force', name)

                except RuntimeError as exc:
                    if 'No such container' not in str(exc):
                        print(f'Could not clean up helper {name}: {exc}', file=sys.stderr)

    def _probe(
            self,
            *,
            donor: ta.Mapping[str, ta.Any],
            target: ta.Mapping[str, ta.Any],
            platform: str,
    ) -> dict[str, ta.Any]:
        require_running(donor)
        require_running(target)

        request = {
            'donor_pid': donor['State']['Pid'],
            'target_pid': target['State']['Pid'],
        }

        identities = self._remote({**request, 'operation': 'probe'}, platform=platform)

        # Bind daemon process IDs to kernel identities, then recheck the daemon's incarnation.

        require_same_incarnation(donor, self._docker.inspect(donor['Id']))
        require_same_incarnation(target, self._docker.inspect(target['Id']))

        return {**request, 'identities': identities}

    def list_mounts(self, target: str | None = None) -> list[dict[str, ta.Any]]:
        target_id = self._docker.inspect(target)['Id'] if target is not None else None

        ids = self._docker.run(
            'container',
            'ls',
            '--all',
            '--quiet',
            '--filter',
            f'label={_LABEL}',
        ).split()

        result = []

        for container_id in ids:
            donor = self._docker.inspect(container_id)
            record = json.loads(donor['Config']['Labels'][_LABEL])

            if target_id is None or record['target_id'] == target_id:
                result.append({
                    'donor': donor['Name'].lstrip('/'),
                    'donor_status': donor['State']['Status'],
                    **record,
                })

        return result

    def cleanup(self, donor_name: str) -> None:
        donor = self._docker.inspect(donor_name)

        labels = donor['Config'].get('Labels') or {}
        if _LABEL not in labels:
            raise RuntimeError('not a hotmount donor')

        record = json.loads(labels[_LABEL])

        # A successful listing distinguishes absence from a failed daemon connection.

        ids = self._docker.run(
            'container',
            'ls',
            '--all',
            '--quiet',
            '--no-trunc',
        ).split()

        if record['target_id'] in ids:
            target = self._docker.inspect(record['target_id'])

            if (
                    target['State']['Running'] and
                    target['State']['StartedAt'] == record['target_started']
            ):
                raise RuntimeError('original target is still running; use unmount instead')

        self._docker.run('container', 'rm', '--force', donor['Id'])

    def unmount(
            self,
            target: str,
            destination: str,
            *,
            lazy: bool = False,
            keep_donor: bool = False,
    ) -> dict[str, ta.Any]:
        destination = normalize_destination(destination)
        target_info = self._docker.inspect(target)

        name = build_donor_name(
            target_id=target_info['Id'],
            destination=destination,
        )

        donor = self._docker.inspect(name)

        record = json.loads(donor['Config']['Labels'][_LABEL])
        if record['target_id'] != target_info['Id'] or record['destination'] != destination:
            raise RuntimeError('donor metadata does not match the requested mount')

        require_running(target_info)
        if target_info['State']['StartedAt'] != record['target_started']:
            raise RuntimeError(f'original target incarnation is gone; run cleanup {name}')

        require_running(donor)

        platform = self._get_platform()

        request = self._probe(
            donor=donor,
            target=target_info,
            platform=platform,
        )

        result = self._remote({
            **request,
            'operation': 'unmount',
            'destination': destination,
            'lazy': lazy,
        }, platform=platform)

        # A lazy detach may leave open files alive. Keep the Desktop share by default in that case.
        if not (keep_donor or lazy):
            self._docker.run(
                'container',
                'rm',
                '--force',
                donor['Id'],
            )

        return {
            **result,
            'donor': name,
            'donor_retained': bool(keep_donor or lazy),
        }

    def mount(
            self,
            target: str,
            *,
            source: str,
            destination: str,
            read_only: bool = False,
            recursive: bool = False,
    ) -> dict[str, ta.Any]:
        destination = normalize_destination(destination)
        if not source or '\x00' in source:
            raise ValueError('invalid source path')

        # Docker validates existence; do not reject an absolute path just because it is remote.

        source = os.path.abspath(os.path.expanduser(source))
        platform = self._get_platform()

        target_info = self._docker.inspect(target)
        require_running(target_info)

        spec = MountSpec(
            target_id=target_info['Id'],
            target_name=target_info['Name'].lstrip('/'),
            target_started=target_info['State']['StartedAt'],
            source=source,
            destination=destination,
            read_only=read_only,
            recursive=recursive,
        )

        name = build_donor_name(
            target_id=spec.target_id,
            destination=destination,
        )

        # The deterministic name is also a daemon-side reservation for this target/destination.

        self._docker.run(
            'create',
            '--name', name,
            '--platform', platform,
            '--network=none',
            '--userns=host',
            '--user=0:0',
            '--cap-drop=ALL',
            '--security-opt=no-new-privileges',
            '--label', f'{_LABEL}={json.dumps(dc.asdict(spec))}',
            '--mount', build_bind_mount(spec),
            '--entrypoint', self._python,
            self._image,
            '-I',
            '-S',
            '-c',
            'import signal; signal.pause()',
        )

        try:
            self._docker.run(
                'container',
                'start',
                name,
            )

            donor = self._docker.inspect(name)

            require_same_incarnation(target_info, self._docker.inspect(spec.target_id))

            request = self._probe(donor=donor, target=target_info, platform=platform)

            result = self._remote({
                **request,
                'operation': 'mount',
                'destination': destination,
                'read_only': read_only,
                'recursive': recursive,
            }, platform=platform)

            require_same_incarnation(target_info, self._docker.inspect(spec.target_id))

        except BaseException:
            # Do not tear down the share if attachment succeeded but the client lost the reply.
            print(f'Donor retained for recovery: {name}; try unmount, or cleanup after target exit.', file=sys.stderr)
            raise

        return {
            **result,
            'donor': name,
            'source': source,
            'target': spec.target_name,
        }


##


def _main() -> None:
    parser = argparse.ArgumentParser(
        description=__doc__,
        formatter_class=argparse.RawDescriptionHelpFormatter,
    )
    parser.add_argument(
        '--docker',
        default='docker',
    )
    parser.add_argument('--context')
    parser.add_argument(
        '--image',
        default=_DEFAULT_IMAGE,
    )
    parser.add_argument(
        '--python',
        default='python3',
        dest='helper_python',
    )
    parser.add_argument(
        '--timeout',
        type=float,
        default=300.,
        help='timeout per Docker CLI invocation, in seconds',
    )
    parser.add_argument(
        '--verbose',
        action='store_true',
    )
    commands = parser.add_subparsers(
        dest='command',
        required=True,
    )

    mount = commands.add_parser(
        'mount',
        help='inject a directory or regular file; missing destinations are created',
    )
    mount.add_argument('target')
    mount.add_argument('source')
    mount.add_argument('destination')
    mount.add_argument(
        '--read-only',
        action='store_true',
    )
    mount.add_argument(
        '--recursive',
        action='store_true',
        help='include existing submounts; unmount may need --lazy',
    )

    unmount = commands.add_parser(
        'unmount',
        help='unmount only the mount recorded by this utility',
    )
    unmount.add_argument('target')
    unmount.add_argument('destination')
    unmount.add_argument(
        '--lazy',
        action='store_true',
        help='detach a busy tree; retain donor until a later normal unmount',
    )
    unmount.add_argument(
        '--keep-donor',
        action='store_true',
    )

    listing = commands.add_parser(
        'list',
        help='list donor records, not a live audit of target mount tables',
    )
    listing.add_argument('target', nargs='?')

    cleanup = commands.add_parser(
        'cleanup',
        help='remove a stale donor after its original target stops/restarts/disappears',
    )
    cleanup.add_argument('donor')

    args = parser.parse_args()

    if args.timeout <= 0:
        parser.error('--timeout must be positive')

    docker = DockerCli(
        executable=args.docker,
        context=args.context,
        timeout=args.timeout,
        verbose=args.verbose,
    )

    mounter = HotMounter(
        docker,
        image=args.image,
        python=args.helper_python,
    )

    try:
        if args.command == 'mount':
            result = mounter.mount(
                args.target,
                source=args.source,
                destination=args.destination,
                read_only=args.read_only,
                recursive=args.recursive,
            )

        elif args.command == 'unmount':
            result = mounter.unmount(
                args.target,
                args.destination,
                lazy=args.lazy,
                keep_donor=args.keep_donor,
            )

        elif args.command == 'list':
            result = mounter.list_mounts(args.target)

        elif args.command == 'cleanup':
            mounter.cleanup(args.donor)
            result = {'status': 'donor-removed', 'donor': args.donor}

        else:
            raise ValueError(args.command)

    except (OSError, RuntimeError, ValueError, subprocess.TimeoutExpired) as exc:
        print(f'error: {exc}', file=sys.stderr)
        raise SystemExit(1) from exc

    except KeyboardInterrupt:
        raise SystemExit(130) from None

    print(json.dumps(result, indent=2))


if __name__ == '__main__':
    _main()
