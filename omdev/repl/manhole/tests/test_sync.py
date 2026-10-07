import os
import threading

import pytest

from ..base import TcpAddress
from ..base import UnixAddress
from ..server import Manhole
from ..sync import SyncThreadManhole
from ..sync import serve_inline
from .utils import Client


##


def _serve_in_thread(manhole, address):
    bound = []
    listening = threading.Event()

    def on_listening(a):
        bound.append(a)
        listening.set()

    thread = threading.Thread(target=serve_inline, args=(manhole, address), kwargs={'on_listening': on_listening})
    thread.start()
    assert listening.wait(10.)
    return thread, bound[0]


def test_inline_over_a_unix_socket(tmp_path):
    path = str(tmp_path / 'inline.sock')
    manhole = Manhole(seed={'answer': 42}, allow_await=False)
    thread, bound = _serve_in_thread(manhole, UnixAddress(path))
    assert bound == UnixAddress(path)

    with Client(bound) as c:
        assert c.prompt().startswith(b'manhole: python')
        assert c.ask('1 + 1') == '2\n'
        assert c.ask('answer') == '42\n'
        assert c.ask('print("a")') == 'a\n'
        assert 'SyntaxError' in c.ask('await answer')  # no loop here, by construction
        c.send('/quit\n')
        assert c.read_eof() == b''

    thread.join(10.)
    assert not thread.is_alive()
    assert not os.path.exists(path)


def test_inline_over_tcp_returns_when_the_client_leaves():
    manhole = Manhole(banner='', allow_await=False)
    thread, bound = _serve_in_thread(manhole, TcpAddress())
    assert isinstance(bound, TcpAddress) and bound.port != 0

    with Client(bound) as c:
        assert c.prompt() == b'>>> '
        assert c.ask('"halted here"') == "'halted here'\n"
        c.send('exit()\n')
        assert c.read_eof() == b''

    thread.join(10.)
    assert not thread.is_alive()


def test_inline_refuses_a_manhole_that_would_await():
    with pytest.raises(Exception, match='allow_await'):
        serve_inline(Manhole(), TcpAddress())


def test_sync_thread_manhole_is_a_stub():
    with pytest.raises(NotImplementedError):
        SyncThreadManhole(Manhole(allow_await=False), TcpAddress()).start()
