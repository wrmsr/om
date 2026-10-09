"""
Ownership of bound IPC socket paths. A binder records the identity of the filesystem entry its bind created, and on
cleanup removes the path only while it is still that entry - never a path some other binder has since created there.
This protects cooperating users of this library, not against a hostile process of the same user.
"""
import fcntl
import os

from omcore import dataclasses as dc


##


@dc.dataclass(frozen=True)
class IpcEntry:
    path: str
    dev: int
    ino: int


def record_ipc_entry(path: str) -> IpcEntry | None:
    try:
        st = os.lstat(path)
    except FileNotFoundError:
        return None
    return IpcEntry(path, st.st_dev, st.st_ino)


def is_ipc_entry_present(entry: IpcEntry) -> bool:
    try:
        st = os.lstat(entry.path)
    except FileNotFoundError:
        return False
    return (st.st_dev, st.st_ino) == (entry.dev, entry.ino)


def unlink_ipc_entry_if_owned(entry: IpcEntry) -> bool:
    """Remove the entry's path if it is still the entry, returning whether it was removed."""

    if not is_ipc_entry_present(entry):
        return False
    try:
        os.unlink(entry.path)
    except FileNotFoundError:
        return False
    return True


##


LEASE_SUFFIX = '.lock'


class IpcLeaseHeldError(Exception):
    pass


class IpcLease:
    """
    An advisory lock on a sidecar file beside a bound IPC path, held for the bind's lifetime. Taken before checking
    for and creating the path, it makes check-then-bind atomic between cooperating binders - including native ones,
    which would otherwise remove an existing path before binding. The lease file is left in place: removing it while
    another binder could lock it would let two binders hold leases on different inodes.
    """

    def __init__(self, fd: int, path: str) -> None:
        super().__init__()

        self._fd: int | None = fd
        self._path = path

    def __repr__(self) -> str:
        return f'{type(self).__name__}<{self._path}>'

    @property
    def path(self) -> str:
        return self._path

    @property
    def held(self) -> bool:
        return self._fd is not None

    @classmethod
    def acquire(cls, socket_path: str) -> IpcLease:
        path = socket_path + LEASE_SUFFIX
        fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_CLOEXEC, 0o600)
        try:
            fcntl.flock(fd, fcntl.LOCK_EX | fcntl.LOCK_NB)
        except BlockingIOError:
            os.close(fd)
            raise IpcLeaseHeldError(path) from None
        except BaseException:
            os.close(fd)
            raise
        return cls(fd, path)

    def release(self) -> None:
        if (fd := self._fd) is not None:
            self._fd = None
            os.close(fd)
