"""
Renderers turn spool records into text for a consumer. They are *stateful* views - one instance per consumer, fed
successive reads in order - so line continuation and incremental decoding work across chunk boundaries. Which fds
are stdout/stderr is a convention of the caller (1 and 2 by default).
"""
import abc
import datetime
import io
import typing as ta

from omcore import lang

from .frames import SpoolRecord
from .text import IncrementalTextDecoder
from .text import split_keeping_newlines


##


class SpoolRenderer(lang.Abstract):
    @abc.abstractmethod
    def render(self, records: ta.Iterable[SpoolRecord]) -> str:
        raise NotImplementedError

    def flush(self) -> str:
        return ''


##


class RawRenderer(SpoolRenderer):
    """Concatenates the payloads of the selected fds (all by default) in arrival order."""

    def __init__(
            self,
            fds: ta.Container[int] | None = None,
            *,
            encoding: str = 'utf-8',
            errors: str = 'replace',
    ) -> None:
        super().__init__()

        self._fds = fds
        self._dec = IncrementalTextDecoder(encoding, errors)

    def render(self, records: ta.Iterable[SpoolRecord]) -> str:
        out = io.StringIO()
        for r in records:
            if self._fds is not None and r.fd not in self._fds:
                continue
            out.write(self._dec.decode(r.fd, r.data))
        return out.getvalue()

    def flush(self) -> str:
        return self._dec.flush()


class ArrivalMergedRenderer(RawRenderer):
    """All fds interleaved by arrival order - the default rendering for foreground tool calls."""

    def __init__(self, *, encoding: str = 'utf-8', errors: str = 'replace') -> None:
        super().__init__(None, encoding=encoding, errors=errors)


##


def _default_ts_format(t_wall_ns: int) -> str:
    dt = datetime.datetime.fromtimestamp(t_wall_ns / 1e9)  # noqa: DTZ006
    return f'{dt:%H:%M:%S}.{(t_wall_ns // 1_000_000) % 1000:03d}'


class TaggedLinesRenderer(SpoolRenderer):
    """
    Prefixes every output line with a fixed-width timestamp and/or an `fd=N` tag, e.g. `12:34:56.789 fd=2| text`.

    - When output switches fd mid-line, a synthetic line break is inserted so tags stay accurate.
    - With `resume_gap_s`, if a line is left open and the next chunk arrives more than that many seconds later, a
      synthetic break is inserted so the model can see that time passed (the new prefix carries a `+` marker).
    - `break_marker` is appended right before every synthetic break (default: nothing).
    """

    def __init__(
            self,
            *,
            timestamps: bool = True,
            fd_tags: bool = True,
            resume_gap_s: float | None = None,
            break_marker: str = '',
            ts_format: ta.Callable[[int], str] = _default_ts_format,
            separator: str = '| ',
            encoding: str = 'utf-8',
            errors: str = 'replace',
    ) -> None:
        super().__init__()

        self._timestamps = timestamps
        self._fd_tags = fd_tags
        self._resume_gap_ns = int(resume_gap_s * 1e9) if resume_gap_s is not None else None
        self._break_marker = break_marker
        self._ts_format = ts_format
        self._separator = separator
        self._dec = IncrementalTextDecoder(encoding, errors)

        self._at_line_start = True
        self._open_fd: int | None = None
        self._last_t_mono_ns: int | None = None

    def _prefix(self, r: SpoolRecord, *, resumed: bool = False) -> str:
        parts: list[str] = []
        if self._timestamps:
            parts.append(self._ts_format(r.t_wall_ns))
        if self._fd_tags:
            parts.append(f'fd={r.fd}')
        if resumed:
            parts.append('+')
        return ' '.join(parts) + self._separator

    def render(self, records: ta.Iterable[SpoolRecord]) -> str:
        out = io.StringIO()
        for r in records:
            text = self._dec.decode(r.fd, r.data)
            if not text:
                continue

            resumed = False
            if not self._at_line_start:
                gap = (
                    self._resume_gap_ns is not None and
                    self._last_t_mono_ns is not None and
                    (r.t_mono_ns - self._last_t_mono_ns) > self._resume_gap_ns
                )
                if r.fd != self._open_fd or gap:
                    out.write(self._break_marker)
                    out.write('\n')
                    self._at_line_start = True
                    resumed = gap

            for piece in split_keeping_newlines(text):
                if self._at_line_start:
                    out.write(self._prefix(r, resumed=resumed))
                    resumed = False
                out.write(piece)
                self._at_line_start = piece.endswith('\n')

            self._open_fd = r.fd
            self._last_t_mono_ns = r.t_mono_ns

        return out.getvalue()

    def flush(self) -> str:
        return self._dec.flush()
