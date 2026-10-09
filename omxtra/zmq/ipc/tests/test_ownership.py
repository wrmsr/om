import os
import socket

import pytest

from ...tests.support import short_tmp_dir
from ..ownership import IpcLease
from ..ownership import IpcLeaseHeldError
from ..ownership import is_ipc_entry_present
from ..ownership import record_ipc_entry
from ..ownership import unlink_ipc_entry_if_owned


def test_lease_is_exclusive_and_reusable():
    with short_tmp_dir() as tmp:
        path = os.path.join(tmp, 'ep')
        a = IpcLease.acquire(path)
        with pytest.raises(IpcLeaseHeldError):
            IpcLease.acquire(path)
        a.release()
        a.release()
        assert not a.held

        # A leftover, unlocked lease file is not a held lease.
        b = IpcLease.acquire(path)
        assert b.held and os.path.exists(path + '.lock')
        b.release()


def test_lease_in_missing_directory_creates_nothing():
    with short_tmp_dir() as tmp:
        with pytest.raises(FileNotFoundError):
            IpcLease.acquire(os.path.join(tmp, 'missing', 'ep'))
        assert os.listdir(tmp) == []


def test_entry_ownership():
    with short_tmp_dir() as tmp:
        path = os.path.join(tmp, 'ep')
        assert record_ipc_entry(path) is None

        s = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s.bind(path)
        entry = record_ipc_entry(path)
        assert entry is not None and is_ipc_entry_present(entry)

        # Replaced: not ours to remove.
        os.unlink(path)
        s2 = socket.socket(socket.AF_UNIX, socket.SOCK_STREAM)
        s2.bind(path)
        assert not unlink_ipc_entry_if_owned(entry)
        assert os.path.exists(path)

        entry2 = record_ipc_entry(path)
        assert entry2 is not None
        assert unlink_ipc_entry_if_owned(entry2)
        assert not os.path.exists(path)
        assert not unlink_ipc_entry_if_owned(entry2)
        s.close()
        s2.close()
