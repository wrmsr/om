"""
The wire protocol: plain text, line at a time, for `nc`, `socat`, `telnet`, or the client in `client.py`. A banner, then
prompts and lines in, outputs out as the code produces them; `/quit` leaves. Nothing here knows how the connection is
transported or on what loop it runs - the dispatcher says where the code runs.
"""
import functools

from ..dispatch import Dispatcher
from ..dispatch import InlineDispatcher
from ..interpreters import Result
from ..interpreters import ResultStatus
from ..lines import LineRepl
from ..lines import handle_line_command
from ..outputs import TextOutputSink
from ..sessions import Session
from .base import Connection


##


_TELNET_IAC = 0xFF
_TELNET_OPTION_COMMANDS = frozenset([0xFB, 0xFC, 0xFD, 0xFE])  # WILL WONT DO DONT, each followed by an option byte


def strip_telnet_commands(data: bytes) -> bytes:
    """Drop telnet's in-band negotiation (IAC sequences) so `telnet` clients work like `nc` ones."""

    if _TELNET_IAC not in data:
        return data

    out = bytearray()
    i = 0
    n = len(data)
    while i < n:
        b = data[i]
        if b != _TELNET_IAC:
            out.append(b)
            i += 1
        elif i + 1 < n and data[i + 1] == _TELNET_IAC:
            out.append(_TELNET_IAC)  # an escaped 0xff data byte
            i += 2
        elif i + 1 < n and data[i + 1] in _TELNET_OPTION_COMMANDS:
            i += 3
        else:
            i += 2
    return bytes(out)


def decode_line(data: bytes) -> str:
    """Bytes off the wire to a line: telnet noise gone, utf-8 leniently, the line ending removed."""

    return strip_telnet_commands(data).decode('utf-8', 'replace').rstrip('\r\n')


##


class ManholeProtocol:
    """One connection's conversation, from banner to goodbye."""

    def __init__(
            self,
            session: Session,
            connection: Connection,
            *,
            banner: str | None = None,
            dispatcher: Dispatcher | None = None,
    ) -> None:
        super().__init__()

        self._session = session
        self._connection = connection
        self._banner = banner
        self._dispatcher = dispatcher if dispatcher is not None else InlineDispatcher()

        # Outputs post straight to the connection as the code produces them - from whatever context the dispatcher
        # runs it in, since posting is thread-safe.
        self._sink = TextOutputSink(connection.post)
        self._repl = LineRepl(session, self._sink)

    @property
    def sink(self) -> TextOutputSink:
        return self._sink

    @property
    def repl(self) -> LineRepl:
        return self._repl

    async def _feed(self, line: str) -> Result | None:
        return await self._repl.feed_line(line)

    async def run(self) -> None:
        connection = self._connection
        repl = self._repl

        if self._banner:
            await connection.write(self._banner.rstrip('\n') + '\n')

        while True:
            await connection.write(repl.prompt)

            line = await connection.read_line()
            if line is None:
                return

            if not repl.pending and (command := handle_line_command(self._session, line, switching=False)) is not None:
                if command.message is not None:
                    await connection.write(command.message + '\n')
                if command.quit:
                    return
                continue

            try:
                result = await self._dispatcher.dispatch(functools.partial(self._feed, line))
            except Exception as e:  # noqa: BLE001
                # Not the code's own error - those are results - but the host's: a busy interpreter, a dispatch failure.
                connection.post(f'error: {e!r}\n')
                repl.reset()
                continue

            if result is not None and result.status is ResultStatus.EXIT:
                return
