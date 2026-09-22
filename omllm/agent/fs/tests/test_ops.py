import os

import pytest

from ..ops import FsFileChangedError
from ..ops import LocalFsOps


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
async def test_local_fs_ops_safe_bounded_glob(tmp_path):
    fs = LocalFsOps()
    root = os.path.realpath(tmp_path)
    for name in ('a.py', 'b.py', 'c.txt'):
        await fs.write_file(os.path.join(root, name), name.encode())

    result = await fs.glob(os.path.join(root, '*.py'), root=root, max_results=1)
    assert len(result.entries) == 1
    assert result.has_more

    with pytest.raises(ValueError, match='outside permitted root'):
        await fs.glob(os.path.join(root, '..', '*.py'), root=root)
