# ruff: noqa: UP006 UP007 UP045
# @om-lite
import fcntl
import os


##


def local_blob_fsync_fd(fd: int, *, full: bool = False) -> None:
    """With full, uses F_FULLFSYNC where available (darwin), which also flushes the drive's write cache."""

    if full and (op := getattr(fcntl, 'F_FULLFSYNC', None)) is not None:
        fcntl.fcntl(fd, op)
    else:
        os.fsync(fd)


def local_blob_fsync_dir(path: str, *, full: bool = False) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        local_blob_fsync_fd(fd, full=full)
    finally:
        os.close(fd)
