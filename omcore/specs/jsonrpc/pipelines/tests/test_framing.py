import pytest

from .....io.pipelines import all as ipl
from ...errors import JsonrpcMessageTooLargeError
from ...errors import JsonrpcProtocolError
from ..framing import ContentLengthJsonrpcFramingHandler
from ..framing import JsonrpcFrame
from ..framing import NdjsonJsonrpcFramingHandler


class Recorder(ipl.Handler):
    def __init__(self):
        super().__init__()
        self.frames = []
        self.errors = []

    def inbound(self, ctx, msg):
        if isinstance(msg, JsonrpcFrame):
            self.frames.append(msg.data)
        elif isinstance(msg, ipl.Messages.Error):
            self.errors.append(msg.exc)
        else:
            ctx.feed_in(msg)


def new_pipeline(handler):
    rec = Recorder()
    p = ipl.Pipeline.new([handler, rec])
    p.feed_initial_input()
    return p, rec


def drain(p):
    out = []
    while (m := p.output.poll()) is not None:
        out.append(m)
    return out


##
# ndjson


def test_ndjson_basic():
    p, rec = new_pipeline(NdjsonJsonrpcFramingHandler(max_frame_bytes=100))
    p.feed_in(b'{"a":1}\n{"b":2}\r\n\n  \n{"c"')
    assert rec.frames == [b'{"a":1}', b'{"b":2}']
    p.feed_in(b':3}\n')
    assert rec.frames == [b'{"a":1}', b'{"b":2}', b'{"c":3}']


def test_ndjson_byte_at_a_time():
    p, rec = new_pipeline(NdjsonJsonrpcFramingHandler(max_frame_bytes=100))
    for b in b'{"a":1}\n{"b":2}\n':
        p.feed_in(bytes([b]))
    assert rec.frames == [b'{"a":1}', b'{"b":2}']


def test_ndjson_trailing_partial_at_eof_is_delivered():
    p, rec = new_pipeline(NdjsonJsonrpcFramingHandler(max_frame_bytes=100))
    p.feed_in(b'{"a":1}\n{"b":2}')
    assert rec.frames == [b'{"a":1}']
    p.feed_final_input()
    assert rec.frames == [b'{"a":1}', b'{"b":2}']


def test_ndjson_oversize_line_is_fatal():
    p, rec = new_pipeline(NdjsonJsonrpcFramingHandler(max_frame_bytes=8))
    p.feed_in(b'{"a":1}\n')
    assert rec.frames == [b'{"a":1}']
    p.feed_in(b'x' * 20)
    assert len(rec.errors) == 1
    assert isinstance(rec.errors[0], JsonrpcMessageTooLargeError)


def test_ndjson_oversize_line_with_newline_is_fatal():
    p, rec = new_pipeline(NdjsonJsonrpcFramingHandler(max_frame_bytes=8))
    p.feed_in(b'x' * 9 + b'\n')
    assert len(rec.errors) == 1
    assert isinstance(rec.errors[0], JsonrpcMessageTooLargeError)


def test_ndjson_exact_size_ok():
    p, rec = new_pipeline(NdjsonJsonrpcFramingHandler(max_frame_bytes=8))
    p.feed_in(b'x' * 8 + b'\n')
    assert rec.frames == [b'x' * 8]
    assert not rec.errors


def test_ndjson_encode():
    p, rec = new_pipeline(NdjsonJsonrpcFramingHandler(max_frame_bytes=100))
    p.feed_in(_Send(JsonrpcFrame(b'{"a":1}')))
    assert [bytes(m) for m in drain(p)] == [b'{"a":1}\n']


def test_ndjson_encode_oversize_raises():
    p, rec = new_pipeline(NdjsonJsonrpcFramingHandler(max_frame_bytes=4))
    p.feed_in(_Send(JsonrpcFrame(b'{"a":1}')))
    # The raise becomes an inbound Error delivered to inner handlers.
    assert len(rec.errors) == 1
    assert isinstance(rec.errors[0], JsonrpcMessageTooLargeError)


##
# content-length


def test_content_length_basic():
    p, rec = new_pipeline(ContentLengthJsonrpcFramingHandler(max_frame_bytes=100))
    p.feed_in(b'Content-Length: 7\r\n\r\n{"a":1}Content-Length: 7\r\nContent-Type: application/vscode-jsonrpc; charset=utf-8\r\n\r\n{"b":2}')  # noqa
    assert rec.frames == [b'{"a":1}', b'{"b":2}']


def test_content_length_byte_at_a_time():
    p, rec = new_pipeline(ContentLengthJsonrpcFramingHandler(max_frame_bytes=100))
    for b in b'Content-Length: 7\r\n\r\n{"a":1}content-length:7\n\n{"b":2}':
        p.feed_in(bytes([b]))
    assert rec.frames == [b'{"a":1}', b'{"b":2}']


def test_content_length_zero_body():
    p, rec = new_pipeline(ContentLengthJsonrpcFramingHandler(max_frame_bytes=100))
    p.feed_in(b'Content-Length: 0\r\n\r\nContent-Length: 2\r\n\r\n{}')
    assert rec.frames == [b'', b'{}']


def test_content_length_missing_header():
    p, rec = new_pipeline(ContentLengthJsonrpcFramingHandler(max_frame_bytes=100))
    p.feed_in(b'Content-Type: x\r\n\r\n')
    assert len(rec.errors) == 1
    assert isinstance(rec.errors[0], JsonrpcProtocolError)


def test_content_length_malformed():
    for data in [
        b'Content-Length: abc\r\n\r\n',
        b'Content-Length: -1\r\n\r\n',
        b'garbage\r\n\r\n',
        b'Content-Length: 1\r\nContent-Length: 2\r\n\r\n',
    ]:
        p, rec = new_pipeline(ContentLengthJsonrpcFramingHandler(max_frame_bytes=100))
        p.feed_in(data)
        assert len(rec.errors) == 1, data
        assert isinstance(rec.errors[0], JsonrpcProtocolError), data


def test_content_length_oversize():
    p, rec = new_pipeline(ContentLengthJsonrpcFramingHandler(max_frame_bytes=8))
    p.feed_in(b'Content-Length: 9\r\n\r\n')
    assert len(rec.errors) == 1
    assert isinstance(rec.errors[0], JsonrpcMessageTooLargeError)


def test_content_length_header_too_long():
    p, rec = new_pipeline(ContentLengthJsonrpcFramingHandler(max_frame_bytes=8, max_header_bytes=16))
    p.feed_in(b'X-Foo: ' + b'y' * 30)
    assert len(rec.errors) == 1
    assert isinstance(rec.errors[0], JsonrpcProtocolError)


def test_content_length_truncated_at_eof():
    p, rec = new_pipeline(ContentLengthJsonrpcFramingHandler(max_frame_bytes=100))
    p.feed_in(b'Content-Length: 7\r\n\r\n{"a"')
    p.feed_final_input()
    assert len(rec.errors) == 1
    assert isinstance(rec.errors[0], JsonrpcProtocolError)


def test_content_length_encode():
    p, rec = new_pipeline(ContentLengthJsonrpcFramingHandler(max_frame_bytes=100))
    p.feed_in(_Send(JsonrpcFrame(b'{"a":1}')))
    assert [bytes(m) for m in drain(p)] == [b'Content-Length: 7\r\n\r\n{"a":1}']


def test_content_length_roundtrip():
    enc = ContentLengthJsonrpcFramingHandler(max_frame_bytes=100)
    p, rec = new_pipeline(enc)
    p.feed_in(_Send(JsonrpcFrame(b'{"a":1}')), _Send(JsonrpcFrame(b'')))
    data = b''.join(bytes(m) for m in drain(p))

    p2, rec2 = new_pipeline(ContentLengthJsonrpcFramingHandler(max_frame_bytes=100))
    p2.feed_in(data)
    assert rec2.frames == [b'{"a":1}', b'']


##


class _Send:
    """Fed inbound; the recorder feeds the wrapped message outbound from the inner end."""

    def __init__(self, msg):
        self.msg = msg


def _recorder_inbound(self, ctx, msg):
    if isinstance(msg, _Send):
        ctx.feed_out(msg.msg)
    elif isinstance(msg, JsonrpcFrame):
        self.frames.append(msg.data)
    elif isinstance(msg, ipl.Messages.Error):
        self.errors.append(msg.exc)
    else:
        ctx.feed_in(msg)


Recorder.inbound = _recorder_inbound  # type: ignore[method-assign]


def test_bad_config():
    with pytest.raises(ValueError):  # noqa
        NdjsonJsonrpcFramingHandler(max_frame_bytes=0)
    with pytest.raises(ValueError):  # noqa
        ContentLengthJsonrpcFramingHandler(max_frame_bytes=1, max_header_bytes=0)
