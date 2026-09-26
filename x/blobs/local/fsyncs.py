import fcntl
import os


##


def fsync_fd(fd: int, *, full: bool = False) -> None:
    """With full, uses F_FULLFSYNC where available (darwin), which also flushes the drive's write cache."""

    if full and (op := getattr(fcntl, 'F_FULLFSYNC', None)) is not None:
        fcntl.fcntl(fd, op)
    else:
        os.fsync(fd)


def fsync_dir(path: str, *, full: bool = False) -> None:
    fd = os.open(path, os.O_RDONLY | os.O_DIRECTORY | os.O_CLOEXEC)
    try:
        fsync_fd(fd, full=full)
    finally:
        os.close(fd)
