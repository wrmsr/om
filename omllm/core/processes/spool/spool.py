"""
The per-process output spool. Loop-agnostic: waiting is delegated to a `SpoolNotifier` supplied by the manager
implementation. Single writer (the manager's reader callbacks); any number of readers, each holding its own cursor.
"""
import abc
import time
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang

from .frames import SpoolRecord
from .frames import decode_frames
from .frames import encode_frame
from .frames import peek_frame_size
from .storage import SpoolStorage


##


class SpoolNotifier(lang.Abstract):
    """A minimal broadcast condition: `notify()` wakes every current `wait()`."""

    @abc.abstractmethod
    def notify(self) -> None:
        raise NotImplementedError

    @abc.abstractmethod
    def wait(self, timeout: float | None) -> ta.Awaitable[bool]:
        """Waits for a notify, returning False on timeout."""

        raise NotImplementedError


class ImmediateSpoolNotifier(SpoolNotifier):
    """Never blocks: for synchronous use (tests, offline readers of a finished spool)."""

    def notify(self) -> None:
        pass

    async def wait(self, timeout: float | None) -> bool:
        return False


NULL_SPOOL_NOTIFIER: ta.Final = ImmediateSpoolNotifier()


##


@ta.final
@dc.dataclass(frozen=True, kw_only=True)
class SpoolRead:
    """
    The out-of-band framing of a read: enough for a tool to phrase truncation, elapsed offsets, and end-of-output to a
    model distinguishably from the process's own bytes.
    """

    records: ta.Sequence[SpoolRecord]

    # The stream range actually returned. Continue reading from `end`.
    start: int
    end: int

    # Framed bytes appended so far; `end < total` (see `more`) means the read was bounded by `max_bytes`.
    total: int

    # Framed bytes between the requested cursor and `start` that were dropped (spilling disabled or failed).
    dropped_before: int = 0

    # No more output will ever arrive (all output pipes closed). NOTE: this is an *output* signal, not a *process* one -
    # a process can close its stdio and keep running, and (they are separate events observed on different threads)
    # output EOF can be seen before the process's exit is. To report exit / the exit code, use `Process.exited` /
    # `Process.returncode` / `await Process.wait(...)`, never this.
    ended: bool = False

    @property
    def more(self) -> bool:
        return self.end < self.total

    @property
    def empty(self) -> bool:
        return not self.records

    def data(self, fd: int | None = None) -> bytes:
        return b''.join(r.data for r in self.records if fd is None or r.fd == fd)


##


class OutputSpool:
    def __init__(
            self,
            storage: SpoolStorage,
            notifier: SpoolNotifier,
            *,
            mono_ns: ta.Callable[[], int] = time.monotonic_ns,
            wall_ns: ta.Callable[[], int] = time.time_ns,
    ) -> None:
        super().__init__()

        self._storage = storage
        self._notifier = notifier
        self._mono_ns = mono_ns
        self._wall_ns = wall_ns

        self._seq = 0
        self._ended = False
        self._num_records = 0
        self._payload_total = 0

    def __repr__(self) -> str:
        return lang.attr_repr(self, 'total', 'ended', with_id=True)

    #

    @property
    def storage(self) -> SpoolStorage:
        return self._storage

    @property
    def total(self) -> int:
        return self._storage.total

    @property
    def payload_total(self) -> int:
        return self._payload_total

    @property
    def num_records(self) -> int:
        return self._num_records

    @property
    def ended(self) -> bool:
        return self._ended

    @property
    def spill_path(self) -> str | None:
        return self._storage.spill_path

    #

    def append(self, fd: int, data: bytes) -> SpoolRecord:
        check.state(not self._ended)
        if not data:
            raise ValueError('Empty append')

        seq = self._seq
        self._seq += 1
        t_mono_ns = self._mono_ns()
        t_wall_ns = self._wall_ns()

        frame = encode_frame(fd, data, t_mono_ns=t_mono_ns, t_wall_ns=t_wall_ns, seq=seq)
        offset = self._storage.append(frame)

        self._num_records += 1
        self._payload_total += len(data)

        self._notifier.notify()

        return SpoolRecord(fd, data, t_mono_ns=t_mono_ns, t_wall_ns=t_wall_ns, seq=seq, offset=offset)

    def mark_ended(self) -> None:
        if self._ended:
            return
        self._ended = True
        self._notifier.notify()

    def close(self, *, keep_spill: bool | None = None) -> None:
        self.mark_ended()
        self._storage.close(keep_spill=keep_spill)

    #

    _READ_CHUNK: ta.ClassVar[int] = 64 * 1024

    def read_available(
            self,
            cursor: int = 0,
            *,
            max_bytes: int | None = None,
    ) -> SpoolRead:
        """
        Synchronously returns whatever is currently available at or after `cursor`. `max_bytes` caps the returned
        payload: records are taken while they fit, except that the first one is always taken (so a read never stalls on
        an oversized record); a read stopped by the cap reports `more`.
        """

        check.arg(cursor >= 0)
        st = self._storage
        total = st.total

        start = st.next_available(cursor)
        dropped = start - cursor

        records: list[SpoolRecord] = []
        pos = start
        payload = 0
        while pos < total:
            buf = st.read(pos, pos + self._READ_CHUNK)
            if not buf:
                break

            # A single frame larger than the chunk: fetch it whole.
            if (fs := peek_frame_size(buf)) is not None and fs > len(buf):
                buf = st.read(pos, pos + fs)

            recs, consumed = decode_frames(
                buf,
                pos,
                max_payload=(max_bytes - payload) if max_bytes is not None else None,
                # The "at least one record" allowance is per read, not per chunk.
                at_least_one=not records,
            )
            if not recs:
                break

            records.extend(recs)
            payload += sum(len(r.data) for r in recs)
            pos += consumed

            if max_bytes is not None and payload >= max_bytes:
                break

            # Stop at the dropped gap - the next read starts after it and reports `dropped_before`.
            if pos != st.next_available(pos):
                break

        return SpoolRead(
            records=records,
            start=start,
            end=pos,
            total=total,
            dropped_before=dropped,
            ended=self._ended,
        )

    async def read(
            self,
            cursor: int = 0,
            *,
            wait: float | None = None,
            max_bytes: int | None = None,
    ) -> SpoolRead:
        """
        Reads at or after `cursor`. With `wait`, keeps collecting for up to that many seconds - returning early only
        when the spool ends or the `max_bytes` cap has been reached (the read could take no more) - so a caller polling
        on behalf of a model gets naturally batched output. Without `wait`, returns whatever is available right now.
        """

        if not wait or wait <= 0:
            return self.read_available(cursor, max_bytes=max_bytes)

        deadline = time.monotonic() + wait
        while True:
            r = self.read_available(cursor, max_bytes=max_bytes)
            if r.ended or r.more or (max_bytes is not None and sum(len(x.data) for x in r.records) >= max_bytes):
                return r
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return r
            await self._notifier.wait(remaining)

    async def poll(
            self,
            cursor: int = 0,
            *,
            timeout: float | None = None,
            max_bytes: int | None = None,
    ) -> SpoolRead:
        """
        Long-poll: returns any currently-available output immediately; if there is none, waits up to `timeout` for the
        first output to arrive (or the spool to end), then returns. Unlike `read`, this does not keep collecting for the
        whole window - it returns as soon as there is something to return, which is what a caller following a running
        process wants.
        """

        r = self.read_available(cursor, max_bytes=max_bytes)
        if r.records or r.ended or not timeout or timeout <= 0:
            return r

        deadline = time.monotonic() + timeout
        while True:
            remaining = deadline - time.monotonic()
            if remaining <= 0:
                return self.read_available(cursor, max_bytes=max_bytes)
            await self._notifier.wait(remaining)
            r = self.read_available(cursor, max_bytes=max_bytes)
            if r.records or r.ended:
                return r

    async def subscribe(
            self,
            cursor: int = 0,
            *,
            max_bytes: int | None = None,
    ) -> ta.AsyncIterator[SpoolRead]:
        """Yields non-empty reads as output arrives, until the spool ends."""

        while True:
            r = self.read_available(cursor, max_bytes=max_bytes)
            if r.records:
                cursor = r.end
                yield r
                continue
            if r.ended:
                return
            await self._notifier.wait(None)
