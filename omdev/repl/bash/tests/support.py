"""
Test support: a stand-in for a bash on a pty which is one as far as the protocol can tell. It reads what is written to
it the way the terminal and the shell do between them - control characters acted on, lines queued behind a foreground
job, a submission decoded back into its source - and answers with prompts. What a submission does is the test's to say:
a handler from its source to a `Reply`.

Nothing here waits: a read with nothing to return times out on the spot, moving a manual clock on by its timeout, and a
read which could never return fails the test instead of hanging it.
"""
import collections
import re
import typing as ta

from omcore import check
from omcore import dataclasses as dc

from ...ptys import PtyProcess
from ...ptys import PtySpawner
from ..protocol import INTERRUPT
from ..protocol import SUSPEND


ReplyItem: ta.TypeAlias = ta.Union[bytes, BaseException, 'Quiet']
ReplyHandler: ta.TypeAlias = ta.Callable[[str], 'Reply']


##


class Cancelled(BaseException):  # noqa
    """A loop's cancellation, as a read sees it: thrown into the caller which is to stop waiting."""


class Quiet:
    """A spell of nothing written: a read with a timeout times out."""


QUIET = Quiet()


class Clock:
    def __init__(self) -> None:
        super().__init__()

        self.now = 0.

    def __call__(self) -> float:
        return self.now


@dc.dataclass(frozen=True, kw_only=True)
class Reply:
    # In order: what the command writes, the quiet spells between, and whatever is thrown into a read along the way.
    output: ta.Sequence[ReplyItem] = ()

    returncode: int = 0
    cwd: str = '/'

    is_running: bool = False  # still in the foreground once the output is written: no prompt until something ends it
    num_interrupts_lost: int = 0  # ...which the first so many interrupts do not
    is_deaf: bool = False  # ...which no interrupt does, though a stop does
    is_stuck: bool = False  # ...which nothing does

    exits_shell: bool = False


##


class ScriptedShell(PtyProcess):
    def __init__(
            self,
            handler: ReplyHandler,
            *,
            clock: Clock,
            argv: ta.Sequence[str],
            size: tuple[int, int],
            comes_up: bool = True,
    ) -> None:
        super().__init__()

        self._handler = handler
        self._clock = clock
        self.argv = tuple(argv)
        self.size = size
        self._comes_up = comes_up

        self.sources: list[str] = []
        self.commands: list[str] = []
        self.num_interrupts = 0
        self.num_suspends = 0
        self.num_stopped_jobs = 0
        self.is_closed = False

        self._nonce: str | None = None
        self._seq = 0
        self._cwd = '/'

        self._out: collections.deque[ReplyItem] = collections.deque()
        self._has_exited = False

        self._typed = b''  # typed, but not yet a line
        self._lines: collections.deque[str] = collections.deque()  # lines the shell has yet to read
        self._block: list[str] | None = None  # the compound command being read
        self._running: Reply | None = None  # the foreground job

    def die(self) -> None:
        """Killed from outside, as far as whoever is talking to it can tell."""

        self._has_exited = True

    def mark(self, seq: int, returncode: int) -> bytes:
        return f'\x1b]7770;{check.not_none(self._nonce)};{seq};{returncode};{self._cwd}\x07'.encode()

    ##
    # The shell

    def _finish(self, returncode: int) -> None:
        self._running = None
        self._out.append(self.mark(self._seq, returncode))
        self._read_lines()

    @staticmethod
    def _decode_block(block: ta.Sequence[str]) -> str:
        data = b''
        for line in block:
            m = check.not_none(re.fullmatch(r"__om_s\+?=\$'(.*)'", line))
            data += re.sub(
                rb'\\x([0-9a-f]{2})',
                lambda x: bytes([int(x.group(1), 16)]),
                m.group(1).encode('ascii'),
            )
        return data.decode('utf-8')

    def _submit(self, source: str) -> None:
        self.sources.append(source)
        reply = self._handler(source)
        self._out.extend(reply.output)

        if reply.exits_shell:
            self._has_exited = True
        elif reply.is_running:
            self._running = reply
        else:
            self._cwd = reply.cwd
            self._out.append(self.mark(self._seq, reply.returncode))

    def _read_line(self, line: str) -> None:
        if 'PROMPT_COMMAND=' in line:
            self._nonce = check.not_none(re.search(r'7770;(\w+);', line)).group(1)
            if self._comes_up:
                # What a real one writes on its way up: its startup files' chatter, and the echo of the line itself.
                self._out.append(b'welcome\r\n' + line.encode() + b'\r\n' + self.mark(0, 0))

        elif self._block is not None:
            if (m := re.fullmatch(r'\}; __om_n=(\d+); __om_rc "\$__om_last"; eval "\$__om_s" </dev/null', line)):
                block, self._block = self._block, None
                self._seq = int(m.group(1))
                self._submit(self._decode_block(block))
            else:
                self._block.append(line)

        elif line == '{':
            self._block = []

        elif (m := re.fullmatch(r' __om_n=(\d+); (.*)', line)):
            self._seq = int(m.group(1))
            self.commands.append(m.group(2))
            if 'kill -KILL' in m.group(2):
                self.num_stopped_jobs = 0
            self._out.append(self.mark(self._seq, 0))

        else:
            raise AssertionError(f'Unexpected line: {line!r}')

    def _read_lines(self) -> None:
        while self._running is None and not self._has_exited and self._lines:
            self._read_line(self._lines.popleft())

    ##
    # The terminal

    def _flush_input(self) -> None:
        self._typed = b''
        self._lines.clear()

    def _interrupt(self) -> None:
        self.num_interrupts += 1
        self._flush_input()

        if (running := self._running) is None:
            # An idle shell abandons the command it was reading and prompts again.
            self._block = None
            self._out.append(b'\r\n' + self.mark(self._seq, 130))
        elif not (running.is_deaf or running.is_stuck):
            if running.num_interrupts_lost:
                self._running = dc.replace(running, num_interrupts_lost=running.num_interrupts_lost - 1)
            else:
                self._out.append(b'\r\n')
                self._finish(130)

    def _suspend(self) -> None:
        self.num_suspends += 1
        self._flush_input()

        if (running := self._running) is not None and not running.is_stuck:
            self.num_stopped_jobs += 1
            self._out.append(b'\r\n[1]+  Stopped\r\n')
            self._finish(148)

    async def write(self, data: bytes) -> None:
        if self.is_closed or self._has_exited:
            raise BrokenPipeError

        for i in range(len(data)):
            c = data[i:i + 1]
            if c == INTERRUPT:
                self._interrupt()
            elif c == SUSPEND:
                self._suspend()
            elif c == b'\n':
                line, self._typed = self._typed, b''
                self._lines.append(line.decode('ascii'))
                self._read_lines()
            else:
                self._typed += c

    async def read(self, timeout: float | None = None) -> bytes | None:
        while self._out:
            item = self._out.popleft()
            if isinstance(item, BaseException):
                raise item
            if isinstance(item, Quiet):
                if timeout is None:
                    continue
                self._clock.now += timeout
                return None
            return item

        if self._has_exited:
            return b''
        if timeout is None:
            raise AssertionError('A read which would never return')
        self._clock.now += timeout
        return None

    async def resize(self, rows: int, cols: int) -> None:
        self.size = (rows, cols)

    async def aclose(self) -> None:
        self.is_closed = True


class ScriptedSpawner(PtySpawner):
    def __init__(
            self,
            handler: ReplyHandler = lambda source: Reply(),
            *,
            comes_up: ta.Callable[[ta.Sequence[str]], bool] = lambda argv: True,
            error: Exception | None = None,
    ) -> None:
        super().__init__()

        self.handler = handler
        self._comes_up = comes_up
        self._error = error

        self.clock = Clock()
        self.shells: list[ScriptedShell] = []

    @property
    def shell(self) -> ScriptedShell:
        return self.shells[-1]

    async def spawn(
            self,
            argv: ta.Sequence[str],
            *,
            rows: int,
            cols: int,
    ) -> PtyProcess:
        if self._error is not None:
            raise self._error

        shell = ScriptedShell(
            lambda source: self.handler(source),
            clock=self.clock,
            argv=argv,
            size=(rows, cols),
            comes_up=self._comes_up(argv),
        )
        self.shells.append(shell)
        return shell
