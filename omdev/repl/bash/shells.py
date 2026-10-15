"""
One live shell, and where the conversation with it stands: the process, the protocol's scanner over what it writes, and
the count of what has been submitted to it. The interpreter decides what is said when; this is how it is said and heard.
"""
import codecs
import collections
import typing as ta

from ..ptys import PtyProcess
from .protocol import INTERRUPT
from .protocol import BashPrompt
from .protocol import BashProtocol


##


class BashShellExitedError(Exception):
    pass


class BashShellGoneError(BashShellExitedError):
    """It had exited before the command at hand could be sent to it: none of that command's doing."""


##


class BashShell:
    """One live shell, and where the conversation with it stands."""

    def __init__(
            self,
            process: PtyProcess,
            protocol: BashProtocol,
            *,
            size: tuple[int, int],
            clock: ta.Callable[[], float],
    ) -> None:
        super().__init__()

        self.process = process
        self.protocol = protocol
        self.size = size
        self._clock = clock

        self._scanner = protocol.new_scanner()
        self._decoder = codecs.getincrementaldecoder('utf-8')(errors='replace')
        self._events: collections.deque[bytes | BashPrompt] = collections.deque()

        self.seq = 0

        # A submission may still be running, its prompt not yet seen: nothing more may be asked of the shell until it
        # has been brought back to one.
        self.is_unsettled = False

    def next_seq(self) -> int:
        self.seq += 1
        return self.seq

    def decode(self, data: bytes) -> str:
        return self._decoder.decode(data)

    async def write(self, data: bytes) -> None:
        try:
            await self.process.write(data)
        except BrokenPipeError:
            raise BashShellExitedError from None

    async def interrupt(self) -> None:
        """
        Interrupts the foreground job: the terminal's interrupt character, which is what reaches it, after SIGINT to the
        shell itself, which the character does not. With that in hand when its job dies of the character's, the shell
        abandons the rest of the submission - rather than going on to its next command as a bash before 4.0 (macOS's)
        does for a job interrupted behind its back. The signal goes first: the shell has to have it before it has the
        job's end, and sent the other way round the two are a race.
        """

        try:
            await self.process.interrupt()
        except BrokenPipeError:
            raise BashShellExitedError from None
        await self.write(INTERRUPT)

    async def read_event(self, timeout: float | None = None) -> bytes | BashPrompt | None:
        """The next run of output or prompt; None when `timeout` passes first. Raises once the shell is gone."""

        deadline = None if timeout is None else self._clock() + timeout
        while not self._events:
            remaining = None if deadline is None else deadline - self._clock()
            if remaining is not None and remaining <= 0:
                return None

            data = await self.process.read(remaining)
            if data is None:
                return None
            if not data:
                raise BashShellExitedError

            self._events.extend(self._scanner.feed(data))

        return self._events.popleft()

    async def wait_prompt(self, seq: int, timeout: float) -> BashPrompt | None:
        """Discards what the shell writes until the prompt of submission `seq`; None when `timeout` passes first."""

        deadline = self._clock() + timeout
        while (remaining := deadline - self._clock()) > 0:
            if (event := await self.read_event(remaining)) is None:
                return None
            if isinstance(event, BashPrompt) and event.seq == seq:
                return event
        return None

    async def run_command(self, command: str, timeout: float) -> BashPrompt | None:
        """Runs one of the conversation's own commands, discarding what it writes; None when it does not finish."""

        seq = self.next_seq()
        await self.write(self.protocol.command(seq, command))
        return await self.wait_prompt(seq, timeout)

    async def query(self, command: str, timeout: float) -> tuple[bytes, BashPrompt] | None:
        """
        Runs one of the conversation's own commands, keeping what it writes - what came before a stale prompt is not its
        - and returns that with its prompt; None when it does not finish.
        """

        seq = self.next_seq()
        await self.write(self.protocol.command(seq, command))

        deadline = self._clock() + timeout
        output = b''
        while (remaining := deadline - self._clock()) > 0:
            if (event := await self.read_event(remaining)) is None:
                return None
            if isinstance(event, BashPrompt):
                if event.seq == seq:
                    return output, event
                output = b''
            else:
                output += event
        return None
