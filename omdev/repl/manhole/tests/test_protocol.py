import collections

from omcore import lang

from ...dispatch import InlineDispatcher
from ...python.interpreter import PythonInterpreter
from ...sessions import Session
from ..base import Connection
from ..base import TcpAddress
from ..base import UnixAddress
from ..base import parse_address
from ..protocol import ManholeProtocol
from ..protocol import decode_line
from ..protocol import strip_telnet_commands


##


class FakeConnection(Connection):
    """Scripted lines in, text out - the protocol with no socket, driven under sync_await."""

    def __init__(self, lines):
        super().__init__()

        self._lines = collections.deque(lines)
        self.out = []
        self.closed = False

    @property
    def peer(self):
        return 'fake'

    async def read_line(self):
        return self._lines.popleft() if self._lines else None

    def post(self, text):
        self.out.append(text)

    async def drain(self):
        pass

    async def aclose(self):
        self.closed = True

    def text(self):
        return ''.join(self.out)


def run(lines, **kwargs):
    session = Session({'python': PythonInterpreter(config=PythonInterpreter.Config(allow_await=False))})
    connection = FakeConnection(lines)
    lang.sync_await(ManholeProtocol(session, connection, **kwargs).run())
    return connection


def test_conversation():
    connection = run(['1 + 1', 'x = 5', 'print("a"); x * 2'], banner='hello')
    assert connection.text() == (
        'hello\n'
        '>>> 2\n'
        '>>> '
        '>>> a\n10\n'
        '>>> '
    )
    assert not connection.closed  # closing is the server's job


def test_continuation_prompts():
    connection = run(['def f(x):', '    return x + 1', '', 'f(1)'], banner='')
    assert connection.text() == '>>> ... ... >>> 2\n>>> '


def test_quit_commands_end_the_conversation():
    for command in ('/quit', '/exit', '/q'):
        connection = run(['1', command, '2'], banner='')
        assert connection.text() == '>>> 1\n>>> '


def test_exit_ends_the_conversation():
    connection = run(['exit()', '2'], banner='')
    assert connection.text() == '>>> '


def test_help_and_unknown_commands():
    connection = run(['/help', '/nope', '/python'], banner='')
    text = connection.text()
    assert '/help  this' in text
    assert '/quit  leave' in text
    assert 'switch to' not in text  # one language, nothing to switch to
    assert 'unknown command: /nope' in text
    assert 'unknown command: /python' in text


def test_slash_lines_mid_block_are_code():
    connection = run(['x = [', '/quit', ']', '', 'x'], banner='')  # the blank line closes the block
    assert 'SyntaxError' in connection.text()
    assert connection.text().endswith('>>> ')


def test_errors_are_reported_and_the_conversation_goes_on():
    connection = run(['1 / 0', '2'], banner='')
    text = connection.text()
    assert 'ZeroDivisionError' in text
    assert text.endswith('>>> 2\n>>> ')


def test_dispatcher_is_used():
    calls = []

    class CountingDispatcher(InlineDispatcher):
        def dispatch(self, fn):
            calls.append(fn)
            return super().dispatch(fn)

    run(['1', '2', '/quit'], banner='', dispatcher=CountingDispatcher())
    assert len(calls) == 2


def test_telnet_noise():
    assert strip_telnet_commands(b'1 + 1\r\n') == b'1 + 1\r\n'
    assert strip_telnet_commands(b'\xff\xfd\x03\xff\xfb\x18' + b'1 + 1\r\n') == b'1 + 1\r\n'
    assert strip_telnet_commands(b'\xff\xf4x') == b'x'
    assert strip_telnet_commands(b'a\xff\xffb') == b'a\xffb'
    assert decode_line(b'\xff\xfd\x031 + 1\r\n') == '1 + 1'
    assert decode_line(b'caf\xc3\xa9\n') == 'café'
    assert decode_line(b'bad \xff\n') == 'bad '


def test_parse_address():
    assert parse_address('/var/run/x.sock') == UnixAddress('/var/run/x.sock')
    assert parse_address('x.sock') == UnixAddress('x.sock')
    assert parse_address(':4242') == TcpAddress(port=4242)
    assert parse_address('10.0.0.1:4242') == TcpAddress(host='10.0.0.1', port=4242)
    assert parse_address('localhost:1') == TcpAddress(host='localhost', port=1)
    assert parse_address('/var/run/odd:1') == UnixAddress('/var/run/odd:1')
