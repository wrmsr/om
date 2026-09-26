import subprocess
import sys
import threading

from ..locks import StripedFileLocks


def test_stripes_stable(tmp_path):
    locks = StripedFileLocks(str(tmp_path), stripes=256)
    assert locks.stripe('abc') == locks.stripe('abc')
    assert locks.path('abc').endswith(f'{locks.stripe("abc"):02x}.lock')
    assert len({locks.stripe(f'k{i}') for i in range(1000)}) > 200


def test_thread_exclusion(tmp_path):
    locks = StripedFileLocks(str(tmp_path))
    held = threading.Event()
    release = threading.Event()

    def holder():
        with locks.lock('k') as ok:
            assert ok
            held.set()
            release.wait()

    t = threading.Thread(target=holder)
    t.start()
    held.wait()
    with locks.lock('k', no_block=True) as ok:
        assert not ok
    release.set()
    t.join()
    with locks.lock('k', no_block=True) as ok:
        assert ok


def test_process_exclusion(tmp_path):
    locks = StripedFileLocks(str(tmp_path))
    code = (
        'import fcntl, os, sys\n'
        'fd = os.open(sys.argv[1], os.O_RDWR | os.O_CREAT)\n'
        'fcntl.flock(fd, fcntl.LOCK_EX)\n'
        'print("locked", flush=True)\n'
        'sys.stdin.readline()\n'
    )
    with subprocess.Popen(
            [sys.executable, '-c', code, locks.path('k')],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True,
    ) as proc:
        assert proc.stdout is not None
        assert proc.stdin is not None
        assert proc.stdout.readline().strip() == 'locked'
        with locks.lock('k', no_block=True) as ok:
            assert not ok
        proc.stdin.write('\n')
        proc.stdin.flush()
        assert proc.wait(timeout=30) == 0
    with locks.lock('k', no_block=True) as ok:
        assert ok
