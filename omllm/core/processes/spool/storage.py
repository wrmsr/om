"""
Byte-level storage for one spool: the framed stream is split into a spilled prefix `[0, spilled_end)` living in a temp
file, an optionally dropped gap `[spilled_end, mem_start)` (only when spilling is disabled or has failed), and an
in-memory suffix `[mem_start, total)`. Not thread-safe: written by one owner.
"""
import collections
import os

from omcore import check
from omcore import lang
from omcore.logs import all as logs


log = logs.get_module_logger(globals())


##


class SpoolStorage:
    def __init__(
            self,
            *,
            memory_cap: int | None,
            spill_dir: str | None = None,
            spill_name: str | None = None,
            keep_spill: bool = False,
    ) -> None:
        super().__init__()

        check.arg(memory_cap is None or memory_cap >= 0)
        self._memory_cap = memory_cap
        self._spill_dir = spill_dir
        self._spill_name = spill_name
        self._keep_spill = keep_spill

        self._frames: collections.deque[bytes] = collections.deque()
        self._mem_size = 0
        self._mem_start = 0
        self._total = 0

        self._spilled_end = 0
        self._spill_fd: int | None = None
        self._spill_path: str | None = None
        self._spill_failed = False

        self._closed = False

    def __repr__(self) -> str:
        return lang.attr_repr(self, 'total', 'spilled_end', 'mem_start', with_id=True)

    #

    @property
    def total(self) -> int:
        return self._total

    @property
    def spilled_end(self) -> int:
        return self._spilled_end

    @property
    def mem_start(self) -> int:
        return self._mem_start

    @property
    def spill_path(self) -> str | None:
        return self._spill_path

    @property
    def spilling(self) -> bool:
        return self._spill_dir is not None and not self._spill_failed

    @property
    def closed(self) -> bool:
        return self._closed

    #

    def is_available(self, offset: int) -> bool:
        return offset < self._spilled_end or offset >= self._mem_start

    def next_available(self, offset: int) -> int:
        """The first available offset at or after `offset` (skips the dropped gap)."""

        if offset < self._spilled_end or offset >= self._mem_start:
            return offset
        return self._mem_start

    #

    def _open_spill(self) -> int | None:
        if self._spill_fd is not None:
            return self._spill_fd
        if self._spill_failed or self._spill_dir is None:
            return None
        try:
            name = self._spill_name or f'spool-{id(self):x}.spool'
            path = os.path.join(self._spill_dir, name)
            fd = os.open(path, os.O_RDWR | os.O_CREAT | os.O_EXCL | getattr(os, 'O_CLOEXEC', 0), 0o600)
        except OSError:
            log.exception('Failed to open spool spill file in %r', self._spill_dir)
            self._spill_failed = True
            return None
        self._spill_fd = fd
        self._spill_path = path
        return fd

    def _evict_oldest(self) -> None:
        f = self._frames.popleft()
        n = len(f)
        self._mem_size -= n

        # The spilled prefix must stay contiguous: once a frame is dropped, everything after it is dropped too, and the
        # file is never appended again (would create a hole).
        if self._spilled_end == self._mem_start and (fd := self._open_spill()) is not None:
            try:
                mv = memoryview(f)
                pos = 0
                while pos < n:
                    pos += os.pwrite(fd, mv[pos:], self._spilled_end + pos)
            except OSError:
                log.exception('Failed to write spool spill file %r; dropping instead', self._spill_path)
                self._spill_failed = True
            else:
                self._spilled_end += n

        self._mem_start += n

    def append(self, frame: bytes) -> int:
        check.state(not self._closed)

        offset = self._total
        self._frames.append(frame)
        n = len(frame)
        self._mem_size += n
        self._total += n

        if (cap := self._memory_cap) is not None:
            while self._mem_size > cap and self._frames:
                self._evict_oldest()

        return offset

    #

    def read(self, start: int, end: int) -> bytes:
        """
        Returns the framed bytes of `[start, end)` intersected with a single available region - either the spilled
        prefix or the memory suffix, never spanning the dropped gap. `start` must be available (see `next_available`).
        Reads may end mid-frame if `end` is not on a boundary; decoders tolerate a trailing partial frame.
        """

        check.state(not self._closed, 'spool storage is closed')
        check.arg(start >= 0)
        end = min(end, self._total)
        if end <= start:
            return b''

        if start < self._spilled_end:
            end = min(end, self._spilled_end)
            fd = check.not_none(self._spill_fd)
            out = bytearray()
            pos = start
            while pos < end:
                b = os.pread(fd, end - pos, pos)
                if not b:
                    break
                out += b
                pos += len(b)
            return bytes(out)

        if start < self._mem_start:
            raise ValueError(f'Offset {start} is in the dropped gap [{self._spilled_end}, {self._mem_start})')

        out = bytearray()
        pos = self._mem_start
        for f in self._frames:
            fe = pos + len(f)
            if fe <= start:
                pos = fe
                continue
            if pos >= end:
                break
            out += f[max(0, start - pos):end - pos]
            pos = fe
        return bytes(out)

    #

    def close(self, *, keep_spill: bool | None = None) -> None:
        """Releases everything: the memory suffix is dropped and the spill file closed (and unlinked unless kept)."""

        if self._closed:
            return
        self._closed = True

        self._frames.clear()
        self._mem_size = 0

        if (fd := self._spill_fd) is not None:
            self._spill_fd = None
            try:
                os.close(fd)
            except OSError:
                log.exception('Failed to close spool spill fd')

            if not (self._keep_spill if keep_spill is None else keep_spill):
                try:
                    os.unlink(check.not_none(self._spill_path))
                except FileNotFoundError:
                    pass
                except OSError:
                    log.exception('Failed to unlink spool spill file %r', self._spill_path)
                else:
                    self._spill_path = None
