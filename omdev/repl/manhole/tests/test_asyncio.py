import asyncio
import os
import stat
import threading

import pytest

from ...asyncio import AsyncioLoopDispatcher
from ..asyncio import AsyncioManholeServer
from ..asyncio import AsyncioThreadManhole
from ..asyncio import start_manhole
from ..base import TcpAddress
from ..base import UnixAddress
from ..server import Manhole
from .utils import Client


##


def sock_path(tmp_path):
    return str(tmp_path / 'manhole.sock')


def test_thread_manhole_over_a_unix_socket(tmp_path):
    path = sock_path(tmp_path)
    mh = start_manhole(path, seed={'answer': 42})
    try:
        running = mh.is_running
        assert running
        bound = mh.address
        assert bound == UnixAddress(path)
        assert stat.S_ISSOCK(os.stat(path).st_mode)
        assert stat.S_IMODE(os.stat(path).st_mode) == 0o600

        with Client(mh.address) as c:
            banner = c.prompt()
            assert banner.startswith(b'manhole: python')
            assert b'/quit to leave' in banner

            assert c.ask('1 + 1') == '2\n'
            assert c.ask('answer') == '42\n'
            assert c.ask('x = answer * 2') == ''
            assert c.ask('x') == '84\n'

            c.send('def f(n):\n')
            c.read_until(b'... ')
            c.send('    return n * 2\n')
            c.read_until(b'... ')
            c.send('\n')
            c.prompt()
            assert c.ask('f(21)') == '42\n'

            assert c.ask('print("a"); print("b", end=""); print("c")') == 'a\nbc\n'

            out = c.ask('1 / 0')
            assert out.startswith('Traceback (most recent call last):')
            assert 'ZeroDivisionError' in out
            assert 'asyncio' not in out  # the user's frames only

            c.send('/quit\n')
            assert c.read_eof() == b''
    finally:
        mh.stop()

    running = mh.is_running
    assert not running
    assert not os.path.exists(path)
    assert not mh.thread.is_alive


def test_tcp_with_an_ephemeral_port():
    with start_manhole(TcpAddress()) as mh:
        address = mh.address
        assert isinstance(address, TcpAddress)
        assert address.host == '127.0.0.1'
        assert address.port != 0
        with Client(address) as c:
            c.prompt()
            assert c.ask('"tcp"') == "'tcp'\n"
            c.send('/quit\n')
            c.read_eof()
    assert mh.address is None


def test_connections_have_their_own_namespaces_and_run_concurrently(tmp_path):
    with start_manhole(sock_path(tmp_path), seed={'threading': threading}) as mh:
        with Client(mh.address) as a, Client(mh.address) as b:
            a.prompt()
            b.prompt()
            assert a.ask('x = 1') == ''
            assert 'NameError' in b.ask('x')
            assert b.ask('x = 2') == ''
            assert a.ask('x') == '1\n'
            assert b.ask('x') == '2\n'
            # The seeded objects are shared, the namespaces are not.
            assert a.ask('threading is not None') == 'True\n'
            a.send('/quit\n')
            b.send('exit()\n')
            assert a.read_eof() == b''
            assert b.read_eof() == b''


def test_stop_with_a_live_client_closes_it(tmp_path):
    mh = start_manhole(sock_path(tmp_path))
    c = Client(mh.address)
    try:
        c.prompt()
        assert c.ask('1') == '1\n'
        mh.stop()
        assert c.read_eof(timeout_s=5.) == b''
    finally:
        c.close()
    assert not mh.thread.is_alive


def test_telnet_clients(tmp_path):
    with start_manhole(sock_path(tmp_path)) as mh, Client(mh.address) as c:
        c.prompt()
        c.send(b'\xff\xfd\x03\xff\xfb\x18' + b'1 + 1\r\n')
        assert c.prompt() == b'2\n>>> '
        c.send('/quit\r\n')
        c.read_eof()


def test_address_in_use_fails_cleanly():
    with start_manhole(TcpAddress()) as mh:
        address = mh.address
        assert isinstance(address, TcpAddress)
        second = AsyncioThreadManhole(Manhole(), TcpAddress(port=address.port))
        with pytest.raises(OSError, match='in use'):
            second.start()
        assert not second.is_running
        assert not second.thread.is_alive


def test_python_native_defaults(tmp_path):
    holder: dict = {}
    with start_manhole(sock_path(tmp_path), seed={'holder': holder}) as mh, Client(mh.address) as c:
        c.prompt()
        assert c.ask('__name__') == "'__manhole__'\n"
        assert c.ask('sys.version_info[0], os.getpid() > 0, gc is not None, threading is not None') == \
            '(3, True, True, True)\n'
        assert c.ask('threading.current_thread().name') == "'om-manhole'\n"

        # A function defined here and called back later from elsewhere in the process still prints to this connection.
        c.send('def report():\n')
        c.read_until(b'... ')
        c.send('    print("reported from", threading.current_thread().name)\n')
        c.read_until(b'... ')
        c.send('\n')
        c.prompt()
        assert c.ask('holder["report"] = report') == ''
        holder['report']()
        assert c.read_until(b'reported from MainThread\n').endswith(b'reported from MainThread\n')

        c.send('/quit\n')
        c.read_eof()


##


async def _aconnect(path):
    reader, writer = await asyncio.open_unix_connection(path)

    async def read_until(marker: bytes) -> bytes:
        buf = b''
        while not buf.endswith(marker):
            data = await asyncio.wait_for(reader.read(65536), 10.)
            if not data:
                raise EOFError(buf)
            buf += data
        return buf

    async def ask(line: str) -> str:
        writer.write(line.encode('utf-8') + b'\n')
        await writer.drain()
        return (await read_until(b'>>> '))[:-4].decode('utf-8')

    return reader, writer, read_until, ask


@pytest.mark.asyncs('asyncio')
async def test_dispatch_to_the_host_loop(tmp_path):
    host_loop = asyncio.get_running_loop()
    path = sock_path(tmp_path)
    mh = start_manhole(
        path,
        seed={'asyncio': asyncio, 'host_loop': host_loop, 'threading': threading},
        dispatcher=AsyncioLoopDispatcher(host_loop),
    )
    try:
        _, writer, read_until, ask = await _aconnect(path)
        await read_until(b'>>> ')
        # The code runs on the host's loop, on the host's thread - not the manhole's.
        assert await ask('asyncio.get_running_loop() is host_loop') == 'True\n'
        assert await ask('threading.current_thread() is threading.main_thread()') == 'True\n'
        assert await ask('await asyncio.sleep(0, result=7)') == '7\n'
        assert await ask('print("streamed"); 1') == 'streamed\n1\n'
        writer.close()
    finally:
        await asyncio.to_thread(mh.stop)


@pytest.mark.asyncs('asyncio')
async def test_server_on_the_hosts_own_loop(tmp_path):
    path = sock_path(tmp_path)
    manhole = Manhole(seed={'asyncio': asyncio}, banner='')
    async with AsyncioManholeServer(UnixAddress(path), manhole.handle) as server:
        bound = server.address
        assert bound == UnixAddress(path)
        _, writer, read_until, ask = await _aconnect(path)
        await read_until(b'>>> ')
        assert server.num_connections == 1
        assert await ask('asyncio.get_running_loop() is not None') == 'True\n'
        assert await ask('await asyncio.sleep(0, result=5)') == '5\n'
        writer.close()
        await writer.wait_closed()
        for _ in range(50):
            if not server.num_connections:
                break
            await asyncio.sleep(.01)
        assert server.num_connections == 0
    bound = server.address
    assert bound is None
    assert not os.path.exists(path)
