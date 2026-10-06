"""
Zero-dependency tests. Place beside hotmount.py.

    python -m unittest -v test_hotmount

Linux kernel tests (isolated disposable user/mount namespaces, no Docker required):

    unshare --user --map-root-user --mount \
        env DOCKERHOTMOUNT_TEST_KERNEL=1 python -m unittest -v test_hotmount.KernelTests

Docker integration test (starts/removes test containers; can run on macOS or Linux):

    DOCKERHOTMOUNT_TEST_DOCKER=1 python -m unittest -v test_hotmount.DockerTests
"""
import contextlib
import csv
import ctypes as ct
import inspect
import io
import json
import os
import select
import signal
import subprocess
import sys
import tempfile
import unittest
import uuid

from .. import hotmount as hm


##


class UnitTests(unittest.TestCase):
    def test_destinations(self):
        for value in ('/', '//', '', 'relative', '/a/../b', '/a/\0b'):
            with self.subTest(value=value), self.assertRaises(ValueError):
                hm.normalize_destination(value)
        self.assertEqual(hm.normalize_destination('//a///b/./'), '/a/b')
        self.assertEqual(hm.normalize_destination('/a b/c,d'), '/a b/c,d')

    def test_donor_name(self):
        a = hm.build_donor_name(target_id='a' * 64, destination='/x')
        self.assertEqual(a, hm.build_donor_name(target_id='a' * 64, destination='/x'))
        self.assertNotEqual(a, hm.build_donor_name(target_id='a' * 64, destination='/y'))
        self.assertNotEqual(a, hm.build_donor_name(target_id='b' * 64, destination='/x'))

    def test_bind_csv(self):
        for source in ('/plain', '/has spaces', '/a,b', '/a"b', '/a\nb'):
            with self.subTest(source=source):
                spec = hm.MountSpec('a', 'target', 'start', source, '/dest', read_only=True)
                fields = next(csv.reader(io.StringIO(hm.build_bind_mount(spec))))
                self.assertIn(f'src={source}', fields)
                self.assertIn('readonly', fields)
                self.assertIn('bind-propagation=rprivate', fields)

    def test_running_and_incarnations(self):
        before = {'Name': '/target', 'State': {'Running': True, 'Pid': 23, 'StartedAt': 'first'}}
        hm.require_same_incarnation(before, before)
        for key, value in (('Pid', 24), ('StartedAt', 'second'), ('Running', False), ('Restarting', True)):
            after = {**before, 'State': {**before['State'], key: value}}
            with self.subTest(key=key), self.assertRaises(RuntimeError):
                hm.require_same_incarnation(before, after)

    @unittest.skipUnless(sys.platform == 'linux', 'Linux proc required')
    def test_payload_self_contained_probe(self):
        request = {'operation': 'probe', 'donor_pid': os.getpid(), 'target_pid': os.getpid()}
        result = run_payload(request)
        self.assertEqual(result['donor'], result['target'])
        self.assertGreater(result['target']['start_ticks'], 0)
        self.assertEqual(len(result['target']['mnt_ns']), 2)


def run_payload(request):
    source = inspect.getsource(hm._do_ctypes_stuff) + '\n_do_ctypes_stuff()\n'
    result = subprocess.run(
        [sys.executable, '-I', '-S', '-c', source, json.dumps(request)],
        stdin=subprocess.DEVNULL, capture_output=True, text=True, timeout=20,
    )
    if result.returncode:
        raise RuntimeError(result.stderr)
    return json.loads(result.stdout)


## Real syscall tests using two tool-free, chrooted processes in separate mount namespaces.


def load_libc():
    libc = ct.CDLL(None, use_errno=True)
    libc.unshare.argtypes = [ct.c_int]
    libc.unshare.restype = ct.c_int
    libc.mount.argtypes = [ct.c_char_p, ct.c_char_p, ct.c_char_p, ct.c_ulong, ct.c_void_p]
    libc.mount.restype = ct.c_int
    libc.umount2.argtypes = [ct.c_char_p, ct.c_int]
    libc.umount2.restype = ct.c_int
    return libc


def check_kernel(result):
    if result == -1:
        err = ct.get_errno()
        raise OSError(err, os.strerror(err))


def run_chroot_child():
    root, source, ready = sys.argv[1:]
    ready = int(ready)
    try:
        libc = load_libc()
        check_kernel(libc.unshare(0x00020000))
        check_kernel(libc.mount(None, b'/', None, (1 << 18) | 16384, None))
        check_kernel(libc.mount(os.fsencode(root), os.fsencode(root), None, 4096, None))
        if source:
            target = os.path.join(root, 'hotmount-source')
            if os.path.isdir(source):
                os.mkdir(target)
            else:
                with open(target, 'w'):
                    pass
            check_kernel(libc.mount(os.fsencode(source), os.fsencode(target), None, 4096 | 16384, None))
        os.chroot(root)
        os.chdir('/')
        os.write(ready, b'R')
        os.close(ready)
        signal.pause()
    except BaseException as exc:
        os.write(ready, repr(exc).encode())
        raise


@contextlib.contextmanager
def chroot_process(root, *, source=None, libc=None):
    payload = 'import ctypes as ct\nimport os\nimport signal\nimport sys\n'
    for function in (load_libc, check_kernel, run_chroot_child):
        payload += inspect.getsource(function) + '\n'
    payload += 'run_chroot_child()\n'
    ready_r, ready_w = os.pipe()
    try:
        proc = subprocess.Popen(
            [sys.executable, '-I', '-S', '-c', payload, root, source or '', str(ready_w)],
            pass_fds=(ready_w,), stdin=subprocess.DEVNULL, stdout=subprocess.PIPE, stderr=subprocess.PIPE,
        )
    except BaseException:
        os.close(ready_r)
        raise
    finally:
        os.close(ready_w)
    try:
        if not select.select([ready_r], [], [], 10)[0]:
            raise RuntimeError('chroot child failed to become ready')
        ready = os.read(ready_r, 4096)
        if ready != b'R':
            raise RuntimeError(f'cannot initialize chroot child: {ready!r}')
        yield proc.pid
    finally:
        os.close(ready_r)
        proc.kill()
        proc.communicate(timeout=10)


@unittest.skipUnless(os.environ.get('DOCKERHOTMOUNT_TEST_KERNEL') == '1', 'opt-in real Linux mount-namespace tests')
class KernelTests(unittest.TestCase):
    def setUp(self):
        self.libc = load_libc()
        check_kernel(self.libc.mount(None, b'/', None, (1 << 18) | 16384, None))
        self.stack = contextlib.ExitStack()
        self.addCleanup(self.stack.close)
        self.temp = self.stack.enter_context(tempfile.TemporaryDirectory())
        self.source = os.path.join(self.temp, 'source')
        self.target_root = os.path.join(self.temp, 'target')
        self.donor_root = os.path.join(self.temp, 'donor')
        os.mkdir(self.source)
        os.mkdir(self.target_root)
        os.mkdir(self.donor_root)
        with open(os.path.join(self.source, 'hello'), 'w') as f:
            f.write('hello from the source')

    def start(self, *, file=False):
        source = os.path.join(self.source, 'hello') if file else self.source
        self.donor_pid = self.stack.enter_context(chroot_process(self.donor_root, source=source, libc=self.libc))
        self.target_pid = self.stack.enter_context(chroot_process(self.target_root, libc=self.libc))
        self.request = {'donor_pid': self.donor_pid, 'target_pid': self.target_pid}
        self.request['identities'] = run_payload({**self.request, 'operation': 'probe'})
        self.target_view = f'/proc/{self.target_pid}/root'

    def mount(self, destination='/injected/deep', *, read_only=False, recursive=False):
        self.destination = destination
        return run_payload({
            **self.request, 'operation': 'mount', 'destination': destination,
            'read_only': read_only, 'recursive': recursive,
        })

    def unmount(self, *, lazy=False):
        return run_payload({
            **self.request, 'operation': 'unmount', 'destination': self.destination, 'lazy': lazy,
        })

    def test_directory_roundtrip_and_no_target_tools(self):
        self.start()
        self.assertEqual(os.listdir(self.target_root), [])
        result = self.mount()
        self.assertEqual(result['status'], 'mounted')
        path = self.target_view + '/injected/deep/hello'
        with open(path) as f:
            self.assertEqual(f.read(), 'hello from the source')
        with open(path, 'w') as f:
            f.write('changed through target')
        with open(os.path.join(self.source, 'hello')) as f:
            self.assertEqual(f.read(), 'changed through target')
        self.assertEqual(self.unmount()['status'], 'detached')
        self.assertEqual(os.listdir(self.target_view + '/injected/deep'), [])
        self.assertEqual(self.unmount()['status'], 'already-detached')

    def test_regular_file(self):
        self.start(file=True)
        self.mount('/config/injected.txt')
        with open(self.target_view + '/config/injected.txt') as f:
            self.assertEqual(f.read(), 'hello from the source')
        self.unmount()
        self.assertEqual(os.stat(self.target_view + '/config/injected.txt').st_size, 0)

    def test_read_only_and_host_still_writable(self):
        self.start()
        self.mount(read_only=True)
        with self.assertRaises(OSError):
            with open(self.target_view + '/injected/deep/hello', 'w'):
                pass
        with open(os.path.join(self.source, 'hello'), 'w') as f:
            f.write('host can still write')
        with open(self.target_view + '/injected/deep/hello') as f:
            self.assertEqual(f.read(), 'host can still write')
        self.unmount()

    def test_busy_and_lazy(self):
        self.start()
        self.mount()
        with open(self.target_view + '/injected/deep/hello') as f:
            with self.assertRaisesRegex(RuntimeError, 'busy'):
                self.unmount()
            self.assertEqual(self.unmount(lazy=True)['status'], 'detached')
            self.assertEqual(f.read(), 'hello from the source')
        self.assertFalse(os.path.exists(self.target_view + '/injected/deep/hello'))

    def test_reject_symlink_parent(self):
        self.start()
        os.symlink('/elsewhere', os.path.join(self.target_root, 'injected'))
        with self.assertRaises(RuntimeError):
            self.mount()

    def test_reject_symlink_destination(self):
        self.start()
        os.symlink('/elsewhere', os.path.join(self.target_root, 'dest'))
        with self.assertRaisesRegex(RuntimeError, 'symlink'):
            self.mount('/dest')

    def test_refuse_overmount_existing_mountpoint(self):
        self.start()
        with self.assertRaisesRegex(RuntimeError, 'already a mountpoint'):
            # / is excluded by the host CLI; create a real mount in target first instead.
            self.destination = '/existing'
            self.mount(self.destination)
            os.unlink(os.path.join(self.donor_root, '.hotmount-receipt.json'))
            self.mount(self.destination)

    def test_reject_stale_identity(self):
        self.start()
        self.request['identities']['target']['start_ticks'] += 1
        with self.assertRaisesRegex(RuntimeError, 'stale PID'):
            self.mount()

    def test_receipt_prevents_duplicate_injection(self):
        self.start()
        self.mount()
        with self.assertRaisesRegex(RuntimeError, 'already has a receipt'):
            self.mount()
        self.unmount()

    def test_existing_files_are_revealed_again(self):
        self.start()
        os.mkdir(os.path.join(self.target_root, 'dest'))
        with open(os.path.join(self.target_root, 'dest', 'original'), 'w') as f:
            f.write('untouched')
        self.mount('/dest')
        self.assertFalse(os.path.exists(self.target_view + '/dest/original'))
        self.unmount()
        with open(self.target_view + '/dest/original') as f:
            self.assertEqual(f.read(), 'untouched')

    def test_recursive_readonly_submounts(self):
        sub = os.path.join(self.source, 'sub')
        os.mkdir(sub)
        check_kernel(self.libc.mount(b'tmpfs', os.fsencode(sub), b'tmpfs', 0, None))
        self.stack.callback(lambda: check_kernel(self.libc.umount2(os.fsencode(sub), 2)))
        with open(os.path.join(sub, 'child'), 'w') as f:
            f.write('nested mount')
        self.start()
        self.mount(read_only=True, recursive=True)
        path = self.target_view + '/injected/deep/sub/child'
        with open(path) as f:
            self.assertEqual(f.read(), 'nested mount')
        with self.assertRaises(OSError):
            with open(path, 'w'):
                pass
        self.unmount(lazy=True)


## Docker/Desktop smoke test. docker exec below is verification, not part of the implementation.


@unittest.skipUnless(os.environ.get('DOCKERHOTMOUNT_TEST_DOCKER') == '1', 'opt-in Docker integration test')
class DockerTests(unittest.TestCase):
    def test_docker_roundtrip(self):
        docker = hm.DockerCli()
        mounter = hm.HotMounter(docker)
        name = f'hotmount-test-{uuid.uuid4().hex}'
        with tempfile.TemporaryDirectory(prefix='hotmount-test-', dir=os.path.expanduser('~')) as temp:
            source = os.path.join(temp, 'source, with spaces')
            os.mkdir(source)
            with open(os.path.join(source, 'hello'), 'w') as f:
                f.write('hello from host')
            docker.run(
                'run',
                '--detach',
                '--name', name,
                '--network=none',
                '--cap-drop=ALL',
                'busybox:1.37',
                'sleep',
                '86400',
            )
            try:
                before = docker.inspect(name)
                result = mounter.mount(name, source=source, destination='/injected/new')
                self.assertEqual(result['status'], 'mounted')
                self.assertEqual(
                    docker.run(
                        'exec',
                        name,
                        'cat',
                        '/injected/new/hello',
                    ),
                    'hello from host',
                )
                docker.run(
                    'exec',
                    name,
                    'sh',
                    '-c',
                    'printf "from target" > /injected/new/hello',
                )
                with open(os.path.join(source, 'hello')) as f:
                    self.assertEqual(f.read(), 'from target')
                self.assertEqual(mounter.unmount(name, '/injected/new')['status'], 'detached')
                docker.run(
                    'exec',
                    name,
                    'test',
                    '!',
                    '-e',
                    '/injected/new/hello',
                )
                hm.require_same_incarnation(before, docker.inspect(name))
                self.assertEqual(mounter.list_mounts(name), [])

                mounter.mount(name, source=source, destination='/readonly', read_only=True)
                with self.assertRaises(RuntimeError):
                    docker.run('exec', name, 'touch', '/readonly/should-fail')
                mounter.unmount(name, '/readonly')

                mounter.mount(name, source=os.path.join(source, 'hello'), destination='/single/file.txt')
                self.assertEqual(docker.run('exec', name, 'cat', '/single/file.txt'), 'from target')
                mounter.unmount(name, '/single/file.txt')
            finally:
                records = mounter.list_mounts(name)
                docker.run('container', 'rm', '--force', name)
                for record in records:
                    mounter.cleanup(record['donor'])
