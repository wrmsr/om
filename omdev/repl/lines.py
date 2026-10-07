"""
The line-oriented read-eval-print core shared by transport frontends: a bare stdin/stdout loop, a socket manhole. Lines
arrive one at a time and accumulate until the active language calls the buffer complete; outputs go to a sink. The
whole-buffer frontends (minitui submits a finished buffer) do not go through this.
"""
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
