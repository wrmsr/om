import os

import pytest

from omcore.io.pipelines.drivers.pure import PureIoPipelineDriver

from ....api.messages import MessageLimits
from ...commands import ZmtpCommand
from ...errors import ZmtpHandshakeError
from ...errors import ZmtpLimitError
from ...errors import ZmtpProtocolError
from ...errors import ZmtpTruncatedError
from ...frames import encode_command_frame
from ...frames import encode_frame_header
from ...greetings import ZmtpGreeting
from ...greetings import encode_greeting
from ..codecs import ZmtpCodecConfig
from ..messages import ZmtpMessage
from .harness import Collector
from .harness import Send
from .harness import codec_spec
from .harness import step


GREETING = encode_greeting(ZmtpGreeting())


def _frame(body: bytes, *, more: bool = False) -> bytes:
    return encode_frame_header(len(body), more=more) + body


def _message(*frames: bytes) -> bytes:
    return b''.join(_frame(f, more=i < len(frames) - 1) for i, f in enumerate(frames))


def _run(*chunks: bytes, config: ZmtpCodecConfig | None = None, eof: bool = False) -> Collector:
    c = Collector()
    d = PureIoPipelineDriver(codec_spec(c, config=config))
    step(d)
    for chunk in chunks:
        d.feed_input(chunk)
        step(d)
    if eof:
        d.feed_eof()
        step(d)
    return c


##


def test_greeting_split_at_every_point():
    for i in range(1, len(GREETING)):
        c = _run(GREETING[:i], GREETING[i:])
        assert c.items == [ZmtpGreeting()]
        assert not c.errors

    c = _run(*[bytes([b]) for b in GREETING])
    assert c.items == [ZmtpGreeting()]


def test_staged_native_greeting_with_padding_and_later_version():
    # Native peers send the signature first, may put data in the padding, and may advertise a later minor version.
    g = bytearray(encode_greeting(ZmtpGreeting(minor=1)))
    g[1:9] = b'\x00\x00\x00\x00\x00\x00\x00\x01'
    c = _run(bytes(g[:10]), bytes(g[10:11]), bytes(g[11:]))
    assert c.items == [ZmtpGreeting(major=3, minor=1)]


def test_greeting_rejected_early():
    c = _run(b'\x00')
    assert len(c.errors) == 1 and isinstance(c.errors[0], ZmtpProtocolError)

    c = _run(GREETING[:9] + b'\x00')
    assert isinstance(c.errors[0], ZmtpProtocolError)

    c = _run(GREETING[:10] + b'\x02')
    assert isinstance(c.errors[0], ZmtpHandshakeError)

    bad = bytearray(GREETING)
    bad[12:16] = b'NU\0L'
    assert isinstance(_run(bytes(bad)).errors[0], ZmtpProtocolError)

    bad = bytearray(GREETING)
    bad[32] = 2
    assert isinstance(_run(bytes(bad)).errors[0], ZmtpProtocolError)


def test_everything_in_one_input():
    data = GREETING + encode_command_frame(b'READY', b'xyz') + _message(b'a', b'b') + _message(b'c')
    c = _run(data)
    assert c.items == [ZmtpGreeting(), ZmtpCommand(b'READY', b'xyz'), ZmtpMessage((b'a', b'b')), ZmtpMessage((b'c',))]


def test_every_split_point_of_frames():
    data = _message(b'', b'x' * 255, b'y' * 256) + encode_command_frame(b'PING', b'') + _message(b'z')
    expected = [ZmtpGreeting(), ZmtpMessage((b'', b'x' * 255, b'y' * 256)), ZmtpCommand(b'PING'), ZmtpMessage((b'z',))]
    for i in range(len(data) + 1):
        for j in range(i, len(data) + 1, 37):
            c = _run(GREETING, data[:i], data[i:j], data[j:])
            assert c.items == expected, (i, j)


def test_frame_sizes():
    sizes = [0, 1, 254, 255, 256, 65536]
    frames = [os.urandom(n) for n in sizes]
    c = _run(GREETING + _message(*frames))
    assert c.items[1:] == [ZmtpMessage(tuple(frames))]

    # A long-form encoding of a small body is valid.
    long_small = bytes([0x02]) + (3).to_bytes(8, 'big') + b'abc'
    c = _run(GREETING + long_small)
    assert c.items[1:] == [ZmtpMessage((b'abc',))]


def test_invalid_frames():
    for bad in [
        bytes([0x08, 0]),  # reserved flag
        bytes([0x80, 0]),  # reserved flag
        bytes([0x05, 0]),  # COMMAND + MORE
        _frame(b'a', more=True) + encode_command_frame(b'READY', b''),  # command inside a message
        bytes([0x04, 0]),  # command without a name
        bytes([0x04, 3, 5, 0x41, 0x41]),  # command name longer than its body
    ]:
        c = _run(GREETING + bad)
        assert len(c.errors) == 1 and isinstance(c.errors[0], ZmtpProtocolError), bad
        assert c.items == [ZmtpGreeting()]


def test_limits_apply_before_the_body_arrives():
    limits = MessageLimits(max_frame_size=100, max_message_size=150, max_frames=3)
    config = ZmtpCodecConfig(limits=limits, max_command_size=50)

    # Exactly at the limits.
    c = _run(GREETING + _message(b'x' * 100, b'y' * 50, b''), config=config)
    assert not c.errors and len(c.items) == 2

    # One over, rejected from the header alone.
    for header in [
        encode_frame_header(101),
        bytes([0x02]) + (1 << 62).to_bytes(8, 'big'),
        bytes([0x02]) + ((1 << 64) - 1).to_bytes(8, 'big'),
        encode_frame_header(51, command=True),
    ]:
        c = _run(GREETING + header, config=config)
        assert len(c.errors) == 1 and isinstance(c.errors[0], ZmtpLimitError), header

    # Too many frames, even empty ones; too many bytes in total, even in small frames.
    c = _run(GREETING + _frame(b'', more=True) * 3 + encode_frame_header(0), config=config)
    assert isinstance(c.errors[0], ZmtpLimitError)
    c = _run(GREETING + _frame(b'x' * 100, more=True) + encode_frame_header(51), config=config)
    assert isinstance(c.errors[0], ZmtpLimitError)


def test_nothing_is_delivered_after_a_violation():
    data = GREETING + _message(b'before') + bytes([0x08, 0]) + _message(b'after')
    c = _run(data, _message(b'later'), eof=True)
    assert c.items == [ZmtpGreeting(), ZmtpMessage((b'before',))]
    assert len(c.errors) == 1
    assert c.final_input


def test_truncation_at_eof():
    complete = GREETING + _message(b'whole')
    for tail in [
        _frame(b'abc')[:1],  # inside a header
        bytes([0x02, 0, 0]),  # inside a long header
        _frame(b'abc')[:3],  # inside a body
        _frame(b'abc', more=True),  # inside a multipart message
    ]:
        c = _run(complete + tail, eof=True)
        assert c.items == [ZmtpGreeting(), ZmtpMessage((b'whole',))]
        assert len(c.errors) == 1 and isinstance(c.errors[0], ZmtpTruncatedError), tail
        assert c.final_input

    c = _run(GREETING[:20], eof=True)
    assert c.items == [] and isinstance(c.errors[0], ZmtpTruncatedError)


def test_clean_eof():
    for data in [b'', GREETING, GREETING + _message(b'a')]:
        c = _run(data, eof=True) if data else _run(eof=True)
        assert not c.errors
        assert c.final_input


@pytest.mark.parametrize('frames', [
    (b'',),
    (b'a', b'', b'c'),
    (b'x' * 300, b'y' * 70000),
    tuple(b'%d' % i for i in range(100)),
])
def test_outbound_encoding_round_trips(frames):
    c = Collector()
    d = PureIoPipelineDriver(codec_spec(c))
    step(d)
    d.enqueue(Send([ZmtpGreeting(), ZmtpCommand(b'READY', b'p'), ZmtpMessage(frames)]))
    step(d)
    data = d.drain_output()
    assert data == GREETING + encode_command_frame(b'READY', b'p') + _message(*frames)

    c2 = _run(data)
    assert c2.items == [ZmtpGreeting(), ZmtpCommand(b'READY', b'p'), ZmtpMessage(frames)]
