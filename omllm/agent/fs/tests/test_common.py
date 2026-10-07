import os

import pytest

from ..common import FsStagedWrite
from ..common import fs_file_digest
from ..common import fs_write_file


def test_staged_write_commit_and_abort(tmp_path):
    root = os.path.realpath(tmp_path)
    path = os.path.join(root, 'file.bin')

    # Staged next to its destination, invisible until the commit, gone from staging afterwards.
    stage = FsStagedWrite(path)
    stage.write(b'one')
    stage.write(b'two')
    assert stage.size == 6
    assert not os.path.exists(path)
    assert len(os.listdir(root)) == 1

    assert stage.commit()
    assert stage.finished
    with open(path, 'rb') as f:  # noqa
        assert f.read() == b'onetwo'
    assert os.listdir(root) == ['file.bin']

    with pytest.raises(RuntimeError):
        stage.write(b'late')
    with pytest.raises(RuntimeError):
        stage.commit()
    stage.abort()  # harmless

    # An abort discards the staging entirely.
    stage = FsStagedWrite(os.path.join(root, 'other.bin'))
    stage.write(b'x')
    stage.abort()
    stage.abort()
    assert stage.finished
    assert os.listdir(root) == ['file.bin']

    # A failed commit cleans up too.
    stage = FsStagedWrite(path)
    stage.write(b'nope')
    with pytest.raises(FileExistsError):
        stage.commit()
    assert stage.finished
    assert os.listdir(root) == ['file.bin']
    with open(path, 'rb') as f:  # noqa
        assert f.read() == b'onetwo'


def test_write_file_is_a_staged_write(tmp_path):
    root = os.path.realpath(tmp_path)
    path = os.path.join(root, 'file.bin')

    assert fs_write_file(path, memoryview(b'abc'))
    assert not fs_write_file(path, b'abcd', overwrite=True, expected_digest=fs_file_digest(b'abc'))
    with open(path, 'rb') as f:  # noqa
        assert f.read() == b'abcd'
    assert os.listdir(root) == ['file.bin']
