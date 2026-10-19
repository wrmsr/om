import os

import pytest

from ..common import FsFileChangedError
from ..local import LocalFsOps


##


@pytest.mark.asyncs('asyncio')
async def test_local_fs_ops(tmp_path):
    fs = LocalFsOps()
    root = os.path.realpath(tmp_path)
    path = os.path.join(root, 'file.txt')

    created = await fs.write_file(path, b'one')
    assert created.created

    first = await fs.read_file(path)
    assert first.data == b'one'

    st = await fs.stat(path)
    assert st.is_file
    assert not st.is_dir
    assert st.size == 3

    with pytest.raises(FileExistsError):
        await fs.write_file(path, b'two')
    assert (await fs.read_file(path)).data == b'one'

    replaced = await fs.write_file(path, b'two', overwrite=True, expected_digest=first.digest)
    assert not replaced.created
    assert (await fs.read_file(path)).data == b'two'

    await fs.write_file(path, b'external change', overwrite=True)

    with pytest.raises(FsFileChangedError):
        await fs.write_file(path, b'three', overwrite=True, expected_digest=first.digest)
    assert (await fs.read_file(path)).data == b'external change'


@pytest.mark.asyncs('asyncio')
async def test_local_fs_ops_stat(tmp_path):
    fs = LocalFsOps()
    root = os.path.realpath(tmp_path)
    path = os.path.join(root, 'file.txt')
    link = os.path.join(root, 'link.txt')
    await fs.write_file(path, b'abc')
    os.symlink(path, link)

    # Following the link as os.stat does, the stat is of the file - except that it says it got there through a link.
    st = await fs.stat(link)
    ost = os.stat(path)
    assert (st.path, st.resolved_path) == (link, path)
    assert (st.is_file, st.is_dir, st.is_symlink) == (True, False, True)
    assert (st.mode, st.ino, st.dev, st.nlink) == (ost.st_mode, ost.st_ino, ost.st_dev, ost.st_nlink)
    assert (st.uid, st.gid, st.size) == (ost.st_uid, ost.st_gid, 3)
    assert (st.atime_ns, st.mtime_ns, st.ctime_ns) == (ost.st_atime_ns, ost.st_mtime_ns, ost.st_ctime_ns)
    assert st.mtime == pytest.approx(ost.st_mtime)
    assert (st.blksize, st.blocks, st.rdev) == (ost.st_blksize, ost.st_blocks, ost.st_rdev)
    assert st.flags == getattr(ost, 'st_flags', None)
    assert st.gen == getattr(ost, 'st_gen', None)

    assert not (await fs.stat(path)).is_symlink

    # And, as os.stat does, it finds nothing at a dangling link.
    dangling = os.path.join(root, 'dangling.txt')
    os.symlink(os.path.join(root, 'missing.txt'), dangling)
    with pytest.raises(FileNotFoundError):
        await fs.stat(dangling)


@pytest.mark.asyncs('asyncio')
async def test_local_fs_ops_glob(tmp_path):
    fs = LocalFsOps()
    root = os.path.realpath(tmp_path)
    for name in ('a.py', 'b.py', 'c.txt'):
        await fs.write_file(os.path.join(root, name), name.encode())
    os.symlink(os.path.join(root, 'missing.py'), os.path.join(root, 'dangling.py'))

    result = await fs.glob(os.path.join(root, '*.py'), max_results=1)
    assert len(result.entries) == 1
    assert result.has_more

    result = await fs.glob(os.path.join(root, '*.py'))
    assert not result.has_more
    by_name = {os.path.basename(e.path): e for e in result.entries}
    assert sorted(by_name) == ['a.py', 'b.py', 'dangling.py']
    assert by_name['a.py'].is_file
    assert by_name['a.py'].resolved_path == os.path.join(root, 'a.py')

    # A dangling link is a match too, described as the link itself and resolved to where it points.
    d = by_name['dangling.py']
    assert (d.is_symlink, d.is_file, d.is_dir) == (True, False, False)
    assert d.resolved_path == os.path.join(root, 'missing.py')

    # Matches keep the pattern's spelling of their paths, and resolve regardless of it.
    result = await fs.glob(os.path.join(root, '.', '*.txt'))
    assert [(e.path, e.resolved_path) for e in result.entries] == [
        (os.path.join(root, '.', 'c.txt'), os.path.join(root, 'c.txt')),
    ]

    with pytest.raises(ValueError, match='must be absolute'):
        await fs.glob('*.py')
