"""A bound on what one command's output costs a frontend, which keeps everything it is given."""
import collections
import typing as ta

from ..outputs import NoteOutput
from ..outputs import OutputSink
from ..outputs import TerminalOutput


##


class LimitedOutput:
    """
    A command's output on its way to the sink, bounded: its first lines as they come, and of what follows only the last
    few, once the command is done - a frontend keeps everything it is given.
    """

    def __init__(
            self,
            sink: OutputSink,
            *,
            max_head_lines: int | None,
            max_tail_lines: int,
    ) -> None:
        super().__init__()

        self._sink = sink

        self._max_head_lines = max_head_lines
        self._max_tail_lines = max_tail_lines
        self._tail: collections.deque[str] = collections.deque(maxlen=max_tail_lines)

        self._num_lines = 0
        self._num_held = 0

    def write_lines(self, lines: ta.Sequence[str]) -> None:
        if not lines:
            return

        head = lines
        if (max_head_lines := self._max_head_lines) is not None:
            room = max(max_head_lines - self._num_lines, 0)
            head = lines[:room]
        self._num_lines += len(lines)

        if head:
            self._sink.write(TerminalOutput('\n'.join(head) + '\n'))

        if (held := lines[len(head):]):
            if not self._num_held:
                if self._max_tail_lines:
                    note = f'only its last {self._max_tail_lines} lines will be shown, once the command has ended'
                else:
                    note = 'it will not be shown'
                self._sink.write(NoteOutput(f'[more output follows: {note}]'))
            self._num_held += len(held)
            self._tail.extend(held)

    def write_partial_line(self, line: str) -> None:
        """A line as far as it has been written: shown as it is while output is shown at all."""

        if self._num_held or (self._max_head_lines is not None and self._num_lines >= self._max_head_lines):
            self.write_lines([line])
        else:
            self._num_lines += 1
            self._sink.write(TerminalOutput(line))

    def finish(self) -> None:
        if not self._num_held:
            return
        if (num_dropped := self._num_held - len(self._tail)):
            self._sink.write(NoteOutput(f'[... {num_dropped} lines not shown ...]'))
        if self._tail:
            self._sink.write(TerminalOutput('\n'.join(self._tail) + '\n'))
        self._num_held = 0
        self._tail.clear()
