"""
The bash interpreter: one long-lived interactive shell on a pty, so what a submission changes - the directory, the
environment, functions, jobs - is there for the next one, and what it runs sees a terminal: colors, line buffering, job
control. Not a terminal emulator: output is reduced to lines (`LineTerminal`), commands get nothing on standard input,
and a program which takes the screen over is stopped and said to be unsupported.

The shell is a `PtyProcess` from a `PtySpawner` - the host's, wherever that puts it - started on first use (and refused
there, unless `Config.no_version_check`, if it is not a bash of at least `MIN_VERSION`), and started again after it
exits or has to be given up on. Everything said to it and heard from it is `BashProtocol`'s.

A caller which stops waiting (a cancellation) leaves its command running, so the command is interrupted there and then
- the terminal's own interrupt character, which reaches the foreground job and nothing else, after SIGINT to the shell
itself, so that it abandons the rest of the submission along with the job (`BashShell.interrupt`) - and the next
execution first makes sure the shell is back at its prompt, escalating to stopping and killing the job, and at last to a
new shell.
"""
import time
import typing as ta

from omcore import dataclasses as dc
from omcore import lang

from ..interpreters import Interpreter
from ..interpreters import InterpreterBusyError
from ..interpreters import InterpreterError
from ..interpreters import Result
from ..interpreters import ResultStatus
from ..languages import BASH_LANGUAGE
from ..languages import Language
from ..outputs import NoteOutput
from ..outputs import OutputSink
from ..ptys import PtySpawner
from ..terminals import LineTerminal
from .limits import LimitedOutput
from .protocol import SUSPEND
from .protocol import BashPrompt
from .protocol import BashProtocol
from .shells import BashShell
from .shells import BashShellExitedError
from .shells import BashShellGoneError


##


class BashStartError(InterpreterError):
    """The shell could not be started, or never reached its first prompt."""


class BashVersionError(BashStartError):
    """The shell is older than the conversation is written for, or did not say it is a bash at all."""


##


class BashInterpreter(Interpreter):
    @dc.dataclass(frozen=True, kw_only=True)
    class Config:
        executable: str = 'bash'

        # Start without the user's startup files. With them, a shell which does not reach its prompt in time is started
        # again without.
        no_rc: bool = False

        # A shell which does not say it is a bash of at least `MIN_VERSION` is refused on startup; this takes its word
        # for it without asking.
        no_version_check: bool = False

        # The terminal's size when the host does not say.
        rows: int = 50
        cols: int = 120

        start_timeout_s: float = 10.

        # How long each step of bringing an interrupted shell back to its prompt is given: the interrupt, then stopping
        # and killing the job, then a new shell.
        interrupt_timeout_s: float = 2.

        # A line still without its newline is shown as it is after this long with nothing more written - a prompt, a
        # progress meter. None waits for the newline.
        partial_line_s: float | None = .5

        # The lines of one command's output passed on as they come; of what it writes past that only the last
        # `max_tail_lines` are, once it has ended. None passes everything.
        max_output_lines: int | None = 4000
        max_tail_lines: int = 1000

    # The oldest bash the conversation is written for - macOS's /bin/bash is still of it.
    MIN_VERSION: ta.ClassVar[tuple[int, int]] = (3, 2)

    def __init__(
            self,
            spawner: PtySpawner,
            *,
            config: Config | None = None,
            size: ta.Callable[[], tuple[int, int]] | None = None,
            clock: ta.Callable[[], float] = time.monotonic,
    ) -> None:
        """`size` is asked for the terminal's (rows, cols) before every command, and the shell's is made to match."""

        super().__init__()

        self._spawner = spawner
        self._config = config if config is not None else self.Config()
        self._size = size
        self._clock = clock

        self._shell: BashShell | None = None
        self._is_busy = False
        self._cwd: str | None = None

    @property
    def language(self) -> Language:
        return BASH_LANGUAGE

    @property
    def config(self) -> Config:
        return self._config

    @property
    def is_started(self) -> bool:
        return self._shell is not None

    @property
    def cwd(self) -> str | None:
        """The shell's working directory as of its last prompt; None before there has been one."""

        return self._cwd

    ##
    # The shell

    def _get_size(self) -> tuple[int, int]:
        if (fn := self._size) is not None:
            rows, cols = fn()
        else:
            rows, cols = self._config.rows, self._config.cols
        return (max(rows, 1), max(cols, 1))

    async def _start_shell(self, *, no_rc: bool) -> BashShell | None:
        config = self._config
        rows, cols = size = self._get_size()

        try:
            process = await self._spawner.spawn(
                [
                    config.executable,
                    *(['--noprofile', '--norc'] if no_rc else []),
                    '--noediting',
                    '-i',
                ],
                rows=rows,
                cols=cols,
            )
        except Exception as e:
            raise BashStartError(f'Could not start {config.executable}: {e}') from e

        shell = BashShell(
            process,
            BashProtocol(),
            size=size,
            clock=self._clock,
        )

        try:
            try:
                await shell.write(shell.protocol.init())
                prompt = await shell.wait_prompt(0, config.start_timeout_s)
            except BashShellExitedError:
                prompt = None

            if prompt is None:
                await process.aclose()
                return None

            if not config.no_version_check:
                await self._check_version(shell)

        except BaseException:
            await process.aclose()
            raise

        self._cwd = prompt.cwd
        return shell

    async def _check_version(self, shell: BashShell) -> None:
        config = self._config

        try:
            reply = await shell.query(shell.protocol.VERSION, config.start_timeout_s)
        except BashShellExitedError:
            reply = None
        if reply is None:
            raise BashStartError(f'{config.executable} did not report its version')

        answer = shell.decode(reply[0]).strip()
        version = shell.protocol.parse_version(answer)
        if version is None or version < self.MIN_VERSION:
            raise BashVersionError(
                f'{config.executable} is not bash {".".join(map(str, self.MIN_VERSION))} or later: {answer!r}',
            )

    async def _start(self, sink: OutputSink) -> BashShell:
        if not self._config.no_rc:
            if (shell := await self._start_shell(no_rc=False)) is not None:
                return shell
            sink.write(NoteOutput('[the shell did not reach its prompt with its startup files: starting without them]'))

        if (shell := await self._start_shell(no_rc=True)) is not None:
            return shell
        raise BashStartError(f'{self._config.executable} did not reach its prompt')

    async def _settle(self, shell: BashShell) -> bool:
        """
        Brings a shell with an abandoned command in flight back to its prompt. The command was sent an interrupt when it
        was abandoned; one which is still there is sent another, then stopped and killed. False when nothing worked.
        """

        timeout = self._config.interrupt_timeout_s
        protocol = shell.protocol

        try:
            if await shell.run_command(protocol.SYNC, timeout) is not None:
                return True

            # An interrupt discards what the terminal has yet to hand the shell - the command just sent with it - so
            # each try sends its own after.
            await shell.interrupt()
            if await shell.run_command(protocol.SYNC, timeout) is not None:
                return True

            await shell.write(SUSPEND)
            if await shell.run_command(protocol.KILL_STOPPED_JOBS, timeout) is not None:
                return True

        except BashShellExitedError:
            pass

        return False

    async def _drop_shell(self) -> None:
        shell, self._shell = self._shell, None
        if shell is not None:
            await shell.process.aclose()

    async def _ensure_shell(self, sink: OutputSink) -> BashShell:
        if (shell := self._shell) is not None and shell.is_unsettled:
            if await self._settle(shell):
                shell.is_unsettled = False
            else:
                await self._drop_shell()
                sink.write(NoteOutput('[the shell did not come back from an interrupt: starting a new one]'))
                shell = None

        if shell is None:
            shell = self._shell = await self._start(sink)

        return shell

    ##
    # Execution

    async def execute(self, source: str, sink: OutputSink) -> Result:
        if self._is_busy:
            raise InterpreterBusyError
        if not source.strip():
            return Result(ResultStatus.OK)

        self._is_busy = True
        try:
            try:
                try:
                    return await self._execute(await self._ensure_shell(sink), source, sink)
                except BashShellGoneError:
                    # It went while nothing was running - killed, or lost with a connection. The command has not run,
                    # and does, in a new one.
                    await self._drop_shell()
                    sink.write(NoteOutput('[the shell was gone: starting a new one]'))
                    return await self._execute(await self._ensure_shell(sink), source, sink)

            except BashShellExitedError:
                await self._drop_shell()
                sink.write(NoteOutput('[the shell exited]'))
                return Result(ResultStatus.EXIT)

        finally:
            self._is_busy = False

    async def _execute(self, shell: BashShell, source: str, sink: OutputSink) -> Result:
        if (size := self._get_size()) != shell.size:
            await shell.process.resize(*size)
            shell.size = size

        seq = shell.next_seq()
        shell.is_unsettled = True
        try:
            try:
                await shell.write(shell.protocol.submit(seq, source))
            except BashShellExitedError:
                raise BashShellGoneError from None

            prompt, was_stopped = await self._follow(shell, seq, sink)

        except BashShellExitedError:
            raise

        except BaseException:
            # The caller has stopped waiting, but the command has not stopped running: it is interrupted now, and the
            # shell stays unsettled for the next execution to deal with.
            try:
                await shell.interrupt()
            except BaseException:  # noqa
                pass
            raise

        if was_stopped:
            killed = await shell.run_command(shell.protocol.KILL_STOPPED_JOBS, self._config.interrupt_timeout_s)
            shell.is_unsettled = killed is None
        else:
            shell.is_unsettled = False
            if prompt.returncode:
                sink.write(NoteOutput(f'[exit {prompt.returncode}]'))

        self._cwd = prompt.cwd
        return Result(
            ResultStatus.OK if not prompt.returncode else ResultStatus.ERROR,
            lang.just(prompt.returncode),
        )

    async def _follow(
            self,
            shell: BashShell,
            seq: int,
            sink: OutputSink,
    ) -> tuple[BashPrompt, bool]:
        """
        Passes what submission `seq` writes on to the sink until its prompt, which is returned along with whether the
        command had to be stopped for taking the screen over.
        """

        config = self._config

        terminal = LineTerminal()
        output = LimitedOutput(
            sink,
            max_head_lines=config.max_output_lines,
            max_tail_lines=config.max_tail_lines,
        )
        was_stopped = False

        try:
            while True:
                event = await shell.read_event(config.partial_line_s if terminal.has_partial_line else None)

                if event is None:
                    if (line := terminal.flush()) is not None:
                        output.write_partial_line(line)

                elif isinstance(event, BashPrompt):
                    # Any other prompt is a stale one: the shell's answer to an interrupt which found it idle.
                    if event.seq == seq:
                        return event, was_stopped

                else:
                    output.write_lines(terminal.feed(shell.decode(event)))

                    if terminal.in_alt_screen and not was_stopped:
                        # Stopped rather than interrupted: an editor shrugs an interrupt off, and the shell takes the
                        # terminal back from a stopped job either way. Said now, not once it has worked: until it has,
                        # this is why nothing is showing.
                        was_stopped = True
                        sink.write(NoteOutput('[full-screen programs are not supported here: stopping it]'))
                        await shell.write(SUSPEND)

        finally:
            # However this ends, what the command got as far as writing is shown.
            if (line := terminal.flush()) is not None:
                output.write_partial_line(line)
            output.finish()

    async def aclose(self) -> None:
        await self._drop_shell()
