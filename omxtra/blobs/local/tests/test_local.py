import datetime
import multiprocessing
import os

import pytest

from ...errors import BlobAlreadyExistsError
from ...errors import BlobNotFoundError
from ...errors import BlobPreconditionFailedError
from ...errors import BlobStreamLengthError
from ...errors import InvalidBlobKeyError
from ...types import BlobPrefix
from ...types import IfAbsent
from ...types import IfMatch
from ..stores import LocalBlobStore


def _store(tmp_path, **kwargs):
    return LocalBlobStore(str(tmp_path), config=LocalBlobStore.Config(**kwargs))


def _tree(root):
    out = []
    for dp, dns, fns in os.walk(root):
        dns[:] = [d for d in dns if d not in ('.tmp', '.locks')] if dp == str(root) else dns
        rel = os.path.relpath(dp, root)
        for n in fns:
            out.append(os.path.normpath(os.path.join(rel, n)))
        for n in dns:
            out.append(os.path.normpath(os.path.join(rel, n)) + '/')
    return sorted(out)


def test_layout(tmp_path):
    s = _store(tmp_path)
    s.put('a', b'1')
    s.put('a/B/c', b'2')
    s.put('caf\u00e9', b'3')
    assert _tree(tmp_path) == [
        'a.dir/',
        'a.dir/%42.dir/',
        'a.dir/%42.dir/c.file',
        'a.file',
        'caf%c3%a9.file',
    ]
    assert sorted(os.listdir(tmp_path)) == ['.locks', '.tmp', 'a.dir', 'a.file', 'caf%c3%a9.file']


def test_foreign_files_ignored(tmp_path):
    s = _store(tmp_path)
    s.put('a/b', b'')
    for n in ['junk.txt', 'A.file', '%61.file', 'x.tmp']:
        with open(os.path.join(tmp_path, n), 'w'):
            pass
    os.mkdir(os.path.join(tmp_path, 'Q.dir'))
    with open(os.path.join(tmp_path, 'Q.dir', 'z.file'), 'w'):
        pass
    with open(os.path.join(tmp_path, 'a.dir', 'notes'), 'w'):
        pass
    assert [i.key for i in s.list()] == ['a/b']
    assert [e.prefix if isinstance(e, BlobPrefix) else e.key for e in s.list_shallow()] == ['a/']


def test_empty_dirs(tmp_path):
    s = _store(tmp_path)
    s.put('a/b/c', b'')
    s.put('x', b'')
    s.delete('a/b/c')
    assert sorted(os.listdir(tmp_path)) == ['.locks', '.tmp', 'x.file']

    os.makedirs(os.path.join(tmp_path, 'e.dir', 'f.dir'))
    assert [i.key for i in s.list()] == ['x']
    assert [e.prefix if isinstance(e, BlobPrefix) else e.key for e in s.list_shallow()] == ['x']
    s.put('e/f/g', b'')
    assert [e.prefix if isinstance(e, BlobPrefix) else e.key for e in s.list_shallow()] == ['e/', 'x']


def test_no_tmp_leftovers(tmp_path):
    s = _store(tmp_path)
    s.put('k', b'x')
    with s.open_writer('w') as w:
        w.write(b'abc')

    def write_then_fail():
        with s.open_writer('w') as w:
            w.write(b'abc')
            raise KeyError

    with pytest.raises(KeyError):
        write_then_fail()
    with pytest.raises(BlobStreamLengthError):
        s.put_stream('p', [b'ab'], length=3)
    with pytest.raises(BlobAlreadyExistsError):
        s.put('k', b'y', cond=IfAbsent())
    with pytest.raises(BlobPreconditionFailedError):
        s.put('k', b'y', cond=IfMatch(s.head('k').version.__class__('nope')))
    with pytest.raises(BlobNotFoundError):
        s.copy('missing', 'c')
    assert os.listdir(os.path.join(tmp_path, '.tmp')) == []
    assert [i.key for i in s.list()] == ['k']


def test_remove_stale_tmp_files(tmp_path):
    s = _store(tmp_path)
    s.put('k', b'')
    tmp_dir = os.path.join(tmp_path, '.tmp')
    for n, age in [('old.tmp', 3600), ('new.tmp', 10), ('other', 3600)]:
        p = os.path.join(tmp_dir, n)
        with open(p, 'w'):
            pass
        t = datetime.datetime.now(tz=datetime.UTC).timestamp() - age
        os.utime(p, (t, t))
    assert s.remove_stale_tmp_files(older_than=datetime.timedelta(minutes=5)) == 1
    assert sorted(os.listdir(tmp_dir)) == ['new.tmp', 'other']


def test_version_churn(tmp_path):
    s = _store(tmp_path, no_fsync=True)
    seen = set()
    prev = s.put('k', b'0000')
    seen.add(prev)
    for i in range(1, 1000):
        v = s.put('k', f'{i:04d}'.encode())
        assert v not in seen
        seen.add(v)
        with pytest.raises(BlobPreconditionFailedError):
            s.put('k', b'xxxx', cond=IfMatch(prev))
        prev = v


def test_key_limits(tmp_path):
    s = _store(tmp_path)
    with pytest.raises(InvalidBlobKeyError):
        s.put('A' * 100, b'')
    with pytest.raises(InvalidBlobKeyError):
        s.put('ok/' + '\u00e9' * 50, b'')
    s.put('a' * 250, b'')
    assert os.listdir(os.path.join(tmp_path, '.tmp')) == []


def test_missing_root(tmp_path):
    s = LocalBlobStore(str(tmp_path / 'nope'))
    with pytest.raises(FileNotFoundError):
        s.put('k', b'')
    with pytest.raises(BlobNotFoundError):
        s.get('k')
    assert list(s.list()) == []


def test_reader_pins_inode(tmp_path):
    s = _store(tmp_path)
    s.put('k', b'old')
    fd = os.open(os.path.join(tmp_path, 'k.file'), os.O_RDONLY)
    try:
        s.put('k', b'new!')
        assert os.pread(fd, 10, 0) == b'old'
    finally:
        os.close(fd)
    assert s.get('k').data == b'new!'


##


def _race_if_absent(root, barrier, i):
    s = LocalBlobStore(root)
    barrier.wait()
    try:
        s.put('race', str(i).encode(), cond=IfAbsent())
    except BlobAlreadyExistsError:
        return False
    return True


def _race_cas(root, barrier, n):
    s = LocalBlobStore(root)
    barrier.wait()
    done = 0
    while done < n:
        b = s.get('ctr')
        try:
            s.put('ctr', str(int(b.data) + 1).encode(), cond=IfMatch(b.info.version))
        except BlobPreconditionFailedError:
            continue
        done += 1


def _race_worker(kind, root, barrier, arg, q):
    try:
        if kind == 'if_absent':
            q.put(_race_if_absent(root, barrier, arg))
        else:
            _race_cas(root, barrier, arg)
            q.put(True)
    except BaseException as e:  # noqa
        q.put(repr(e))


def test_cross_process_races(tmp_path):
    ctx = multiprocessing.get_context('spawn')
    n = 4
    root = str(tmp_path)

    def run(kind, arg_of):
        barrier = ctx.Barrier(n)
        q = ctx.Queue()
        procs = [ctx.Process(target=_race_worker, args=(kind, root, barrier, arg_of(i), q)) for i in range(n)]
        for p in procs:
            p.start()
        results = [q.get(timeout=60) for _ in procs]
        for p in procs:
            p.join(timeout=60)
        return results

    results = run('if_absent', lambda i: i)
    assert sorted(results, key=repr) == sorted([True] + [False] * (n - 1), key=repr), results

    LocalBlobStore(root).put('ctr', b'0')
    results = run('cas', lambda i: 10)
    assert results == [True] * n, results
    assert int(LocalBlobStore(root).get('ctr').data) == n * 10
