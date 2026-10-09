import gc
import weakref

import pytest

from omcore.io.pipelines.drivers.pure import PureIoPipelineDriver

from ....core.sockettypes import SocketType
from ...commands import ZmtpCommand
from ...commands import encode_error
from ...commands import encode_metadata
from ...commands import encode_ready
from ...errors import ZmtpHandshakeError
from ...errors import ZmtpHandshakeTimeoutError
from ...errors import ZmtpPeerError
from ...errors import ZmtpProtocolError
from ...frames import encode_command_frame
from ...frames import encode_frame_header
from ...greetings import ZmtpGreeting
from ...greetings import encode_greeting
from ..messages import ZmtpMessage
from ..messages import ZmtpPeerReady
from .harness import Collector
from .harness import Link
from .harness import Send
from .harness import step
from .harness import zmtp_spec


GREETING = encode_greeting(ZmtpGreeting())


def _cmd(c: ZmtpCommand) -> bytes:
    return encode_command_frame(c.name, c.data)


def _msg(*frames: bytes) -> bytes:
    return b''.join(encode_frame_header(len(f), more=i < len(frames) - 1) + f for i, f in enumerate(frames))


def _pair(a_type, b_type, *, a_identity=b'', b_identity=b'', chunk=None):
    ca, cb = Collector(), Collector()
    a = PureIoPipelineDriver(zmtp_spec(ca, a_type, identity=a_identity))
    b = PureIoPipelineDriver(zmtp_spec(cb, b_type, identity=b_identity))
    link = Link(a, b, chunk=chunk)
    link.pump()
    return link, ca, cb


def _raw(socket_type=SocketType.DEALER, *, timeout_s=None):
    c = Collector()
    d = PureIoPipelineDriver(zmtp_spec(c, socket_type, timeout_s=timeout_s))
    step(d)
    return d, c


def _feed(d, data):
    d.feed_input(data)
    step(d)


##


@pytest.mark.parametrize('chunk', [None, 1, 7])
@pytest.mark.parametrize(('a_type', 'b_type'), [
    (SocketType.DEALER, SocketType.ROUTER),
    (SocketType.ROUTER, SocketType.ROUTER),
    (SocketType.DEALER, SocketType.DEALER),
    (SocketType.PUB, SocketType.SUB),
])
def test_handshake_and_traffic(a_type, b_type, chunk):
    ids = {SocketType.DEALER: b'dealer-id', SocketType.ROUTER: b'router-id'}
    link, ca, cb = _pair(a_type, b_type, a_identity=ids.get(a_type, b''), b_identity=ids.get(b_type, b''), chunk=chunk)

    assert ca.of_type(ZmtpPeerReady) == [ZmtpPeerReady(b_type, ids.get(b_type, b''), ca.items[0].properties)]
    assert cb.of_type(ZmtpPeerReady)[0].socket_type == a_type
    assert cb.of_type(ZmtpPeerReady)[0].identity == ids.get(a_type, b'')
    assert not ca.errors and not cb.errors

    link.a.enqueue(Send([ZmtpMessage((b'one', b'')), ZmtpMessage((b'two',))]))
    link.b.enqueue(Send([ZmtpMessage((b'three',))]))
    link.pump()
    assert ca.of_type(ZmtpMessage) == [ZmtpMessage((b'three',))]
    assert cb.of_type(ZmtpMessage) == [ZmtpMessage((b'one', b'')), ZmtpMessage((b'two',))]


@pytest.mark.parametrize(('a_type', 'b_type'), [
    (SocketType.PUB, SocketType.DEALER),
    (SocketType.PUB, SocketType.PUB),
    (SocketType.SUB, SocketType.ROUTER),
    (SocketType.DEALER, SocketType.SUB),
])
def test_incompatible_peers_fail(a_type, b_type):
    _, ca, cb = _pair(a_type, b_type)
    assert not ca.of_type(ZmtpPeerReady) and not cb.of_type(ZmtpPeerReady)
    assert len(ca.errors) == 1 and isinstance(ca.errors[0], ZmtpHandshakeError)
    assert len(cb.errors) == 1 and isinstance(cb.errors[0], ZmtpHandshakeError)


def test_greeting_sent_at_once_and_ready_after_peer_greeting():
    d, c = _raw()
    assert d.drain_output() == GREETING

    _feed(d, GREETING[:63])
    assert d.drain_output() == b''
    _feed(d, GREETING[63:])
    assert d.drain_output() == _cmd(encode_ready(SocketType.DEALER))

    _feed(d, _cmd(encode_ready(SocketType.ROUTER)) + _msg(b'hi'))
    assert c.items == [ZmtpPeerReady(SocketType.ROUTER, b'', c.items[0].properties), ZmtpMessage((b'hi',))]


def test_later_minor_version_peer():
    d, c = _raw()
    _feed(d, encode_greeting(ZmtpGreeting(minor=1)) + _cmd(encode_ready(SocketType.ROUTER)))
    assert c.of_type(ZmtpPeerReady) and not c.errors


@pytest.mark.parametrize('bad', [
    encode_greeting(ZmtpGreeting(mechanism=b'PLAIN')),
    encode_greeting(ZmtpGreeting(as_server=True)),
    GREETING + _msg(b'too early'),
    GREETING + _cmd(ZmtpCommand(b'HELLO', b'')),
    GREETING + _cmd(ZmtpCommand(b'READY', encode_metadata([('Identity', b'x')]))),
    GREETING + _cmd(ZmtpCommand(b'READY', encode_metadata([('Socket-Type', b'ROUTER'), ('socket-type', b'DEALER')]))),
    GREETING + _cmd(ZmtpCommand(b'READY', encode_metadata([('Socket-Type', b'NOPE')]))),
    GREETING + _cmd(ZmtpCommand(b'READY', b'\x05Socke')),
    GREETING + _cmd(encode_ready(SocketType.REP)),
    GREETING + _cmd(encode_ready(SocketType.ROUTER)) + _cmd(encode_ready(SocketType.ROUTER)),
])
def test_handshake_violations(bad):
    d, c = _raw()
    _feed(d, bad)
    assert len(c.errors) == 1 and isinstance(c.errors[0], ZmtpProtocolError), c.errors
    assert not any(isinstance(i, ZmtpMessage) for i in c.items)


def test_metadata_names_are_case_insensitive_and_unknown_ones_skipped():
    d, c = _raw()
    props = encode_metadata([('X-Custom', b'v'), ('socket-TYPE', b'ROUTER'), ('IDENTITY', b'rid'), ('X-Custom', b'w')])
    _feed(d, GREETING + _cmd(ZmtpCommand(b'READY', props)))
    (ready,) = c.of_type(ZmtpPeerReady)
    assert (ready.socket_type, ready.identity) == (SocketType.ROUTER, b'rid')


def test_peer_error_is_fatal():
    d, c = _raw()
    _feed(d, GREETING + _cmd(encode_error(b'go away')))
    assert len(c.errors) == 1 and isinstance(c.errors[0], ZmtpPeerError)
    assert c.errors[0].reason == b'go away'

    d, c = _raw()
    _feed(d, GREETING + _cmd(encode_ready(SocketType.ROUTER)) + _msg(b'ok') + _cmd(encode_error(b'later')))
    assert c.of_type(ZmtpMessage) == [ZmtpMessage((b'ok',))]
    assert isinstance(c.errors[0], ZmtpPeerError)


def test_unknown_commands_after_handshake_are_ignored():
    d, c = _raw()
    _feed(d, GREETING + _cmd(encode_ready(SocketType.ROUTER)) + _cmd(ZmtpCommand(b'PING', b'\0\0')) + _msg(b'x'))
    assert c.of_type(ZmtpMessage) == [ZmtpMessage((b'x',))]
    assert not c.errors


def test_handshake_deadline_is_absolute():
    d, c = _raw(timeout_s=10.)
    for b in GREETING[:40]:
        d.advance_time(.2)
        _feed(d, bytes([b]))
    assert not c.errors
    d.advance_time(2.)
    step(d)
    assert len(c.errors) == 1 and isinstance(c.errors[0], ZmtpHandshakeTimeoutError)


def test_handshake_deadline_cancelled_on_ready():
    d, c = _raw(timeout_s=10.)
    _feed(d, GREETING + _cmd(encode_ready(SocketType.ROUTER)))
    assert c.of_type(ZmtpPeerReady)
    assert d.next_deadline() is None
    d.advance_time(100.)
    step(d)
    assert not c.errors


def test_handshake_deadline_cancelled_on_eof():
    d, c = _raw(timeout_s=10.)
    d.feed_eof()
    step(d)
    assert c.final_input
    assert d.next_deadline() is None


def test_manual_reads_progress_through_the_handshake_byte_at_a_time():
    # Each side reads only when asked; with one byte moved per step every stage must keep asking for more.
    link, ca, cb = _pair(SocketType.DEALER, SocketType.ROUTER, chunk=1)
    assert ca.of_type(ZmtpPeerReady) and cb.of_type(ZmtpPeerReady)
    link.a.enqueue(Send([ZmtpMessage((b'x' * 1000, b'y'))]))
    link.pump()
    assert cb.of_type(ZmtpMessage) == [ZmtpMessage((b'x' * 1000, b'y'))]


def test_pipeline_released_without_cycle_collection():
    gc.collect()
    gc.disable()
    try:
        d, c = _raw(timeout_s=10.)
        _feed(d, GREETING[:30])
        d.close()
        ref = weakref.ref(d.pipeline)
        del d, c
        assert ref() is None
    finally:
        gc.enable()
