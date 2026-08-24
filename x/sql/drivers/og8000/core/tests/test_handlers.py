import pytest

from omcore import dataclasses as dc
from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineMessages

from ...errors import DatabaseError
from ...errors import InterfaceError
from ...protocol import messages as msgs
from ...protocol.codes import TransactionStatus
from ...protocol.decoding import BackendMessageDecoder
from ...protocol.encoding import FrontendMessageEncoder
from ...protocol.session import ProtocolSession
from ..handlers import OperationDone
from ..handlers import OperationRequest
from ..handlers import PgBackendMessageDecoderIoPipelineHandler
from ..handlers import PgFrontendMessageEncoderIoPipelineHandler
from ..handlers import make_pipeline_spec


@dc.dataclass(frozen=True)
class Send:
    """Fed inbound to the recorder to have it feed the wrapped message outbound from the inner end."""

    msg: object


class Recorder(IoPipelineHandler):
    def __init__(self):
        super().__init__()
        self.received = []

    def inbound(self, ctx, msg):
        if isinstance(msg, Send):
            ctx.feed_out(msg.msg)
        elif isinstance(msg, msgs.BackendMessage):
            self.received.append(msg)
        else:
            ctx.feed_in(msg)


def new_pipeline(*handlers):
    rec = Recorder()
    p = IoPipeline.new([*handlers, rec])
    p.feed_in(IoPipelineMessages.InitialInput())
    drain(p)
    return p, rec


def drain(pipeline):
    out = []
    while (msg := pipeline.output.poll()) is not None:
        out.append(msg)
    return out


##
# Codec handlers


def test_encoder_handler():
    p, _ = new_pipeline(PgFrontendMessageEncoderIoPipelineHandler(FrontendMessageEncoder()))
    p.feed_in(Send(msgs.Sync()))
    p.feed_in(Send('passthrough'))
    assert drain(p) == [b'S\x00\x00\x00\x04', 'passthrough']


def test_decoder_handler_reassembles_fragments():
    p, rec = new_pipeline(PgBackendMessageDecoderIoPipelineHandler(BackendMessageDecoder()))
    wire = (
        b'Z\x00\x00\x00\x05I'
        b'C\x00\x00\x00\x0dSELECT 1\x00'
        b'1\x00\x00\x00\x04'
    )
    for i in range(len(wire)):
        p.feed_in(wire[i:i + 1])
    assert rec.received == [
        msgs.ReadyForQuery(TransactionStatus.IDLE),
        msgs.CommandComplete('SELECT 1'),
        msgs.ParseComplete(),
    ]


def test_decoder_handler_ssl_response():
    p, rec = new_pipeline(PgBackendMessageDecoderIoPipelineHandler(BackendMessageDecoder()))
    p.feed_in(Send(msgs.SslRequest()))
    drain(p)
    p.feed_in(b'S' + b'Z\x00\x00\x00\x05I')
    assert rec.received == [msgs.SslResponse(True), msgs.ReadyForQuery(TransactionStatus.IDLE)]

    rec.received.clear()
    p.feed_in(Send(msgs.SslRequest()))
    drain(p)
    p.feed_in(b'N')
    assert rec.received == [msgs.SslResponse(False)]


##
# Session handler


def new_session_pipeline():
    session = ProtocolSession(user=b'u', password=b'pw', startup_params={'user': b'u'})
    p, _ = new_pipeline(*make_pipeline_spec(session).handlers)
    return session, p


def test_session_handler_runs_operations_end_to_end():
    session, p = new_session_pipeline()
    enc = FrontendMessageEncoder()

    op = session.startup()
    p.feed_in(OperationRequest(op))
    assert drain(p) == [enc.encode(msgs.StartupMessage({'user': b'u'}))]

    p.feed_in(b'R\x00\x00\x00\x08\x00\x00\x00\x03')
    assert drain(p) == [enc.encode(msgs.PasswordMessage(b'pw'))]

    p.feed_in(b'R\x00\x00\x00\x08\x00\x00\x00\x00' + b'Z\x00\x00\x00\x05I')
    assert drain(p) == [OperationDone(op)]
    assert op.done
    assert op.result() is None

    op2 = session.execute_simple('select 1')
    p.feed_in(OperationRequest(op2))
    assert drain(p) == [enc.encode(msgs.Query('select 1'))]
    p.feed_in(b'E\x00\x00\x00\x0fSERROR\x00C0\x00\x00' + b'Z\x00\x00\x00\x05I')
    assert drain(p) == [OperationDone(op2)]
    with pytest.raises(DatabaseError) as ei:
        op2.result()
    assert ei.value.args[0]['C'] == '0'


def test_session_handler_fails_operation_on_eof():
    session, p = new_session_pipeline()
    op = session.execute_simple('select 1')
    p.feed_in(OperationRequest(op))
    drain(p)
    p.feed_in(IoPipelineMessages.FinalInput())
    assert OperationDone(op) in drain(p)
    assert op.done
    with pytest.raises(InterfaceError, match='network error'):
        op.result()
