"""
The line-oriented read-eval-print core shared by transport frontends: a bare stdin/stdout loop, a socket manhole. Lines
arrive one at a time and accumulate until the active language calls the buffer complete; outputs go to a sink. The
whole-buffer frontends (minitui submits a finished buffer) do not go through this.
"""
from omcore import dataclasses as dc
from omcore import lang

from .interpreters import Result
from .languages import Completeness
from .outputs import OutputSink
from .sessions import Session


##


class LineRepl:
    def __init__(
            self,
            session: Session,
            sink: OutputSink,
    ) -> None:
        super().__init__()

        self._session = session
        self._sink = sink

        self._buffer: list[str] = []

    @property
    def session(self) -> Session:
        return self._session

    @property
    def pending(self) -> bool:
        """Whether lines are buffered awaiting completion."""

        return bool(self._buffer)

    @property
    def prompt(self) -> str:
        language = self._session.active.language
        return language.continuation_prompt if self._buffer else language.prompt

    def reset(self) -> None:
        self._buffer.clear()

    async def feed_line(self, line: str) -> Result | None:
        """
        Add a line. Returns the result of the execution the line completed, or None when more lines are needed (or the
        completed buffer was blank).
        """

        self._buffer.append(line)
        source = '\n'.join(self._buffer)

        if self._session.active.language.check_complete(source) is Completeness.INCOMPLETE:
            return None

        self._buffer.clear()
        if not source.strip():
            return None

        return await self._session.execute(source, self._sink)


##


@dc.dataclass(frozen=True)
class LineCommandResult(lang.Final):
    quit: bool = False
    message: str | None = None


QUIT_COMMANDS: frozenset[str] = frozenset(['quit', 'exit', 'q'])


def handle_line_command(
        session: Session,
        line: str,
        *,
        switching: bool = True,
) -> LineCommandResult | None:
    """
    The line frontends' shared slash commands - `/quit`, `/help`, and with `switching` `/<name>` to switch
    interpreters - or None when `line` is not one. Frontends ask only when no lines are pending; mid-block a slash line
    is code.
    """

    if not line.startswith('/'):
        return None

    name, _, _ = line[1:].strip().partition(' ')

    if name in QUIT_COMMANDS:
        return LineCommandResult(quit=True)

    if name == 'help':
        return LineCommandResult(message='\n'.join([
            *((f'/{n}  switch to {n}' for n in session.names) if switching else ()),
            '/help  this',
            '/quit  leave',
        ]))

    if switching and name in session.names:
        session.switch(name)
        return LineCommandResult()

    return LineCommandResult(message=f'unknown command: /{name}')
