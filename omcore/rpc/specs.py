# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import typing as ta

from ..io.pipelines.bytes.buffers import OutboundBytesBufferIoPipelineHandler
from ..io.pipelines.core import IoPipeline
from ..io.pipelines.core import IoPipelineHandler
from ..io.pipelines.core import IoPipelineMetadata
from ..io.pipelines.core import IoPipelineService
from ..io.pipelines.flow.stub import StubIoPipelineFlowService
from ..io.pipelines.sched.timeouts import IdleStateIoPipelineHandler
from ..io.pipelines.sched.timeouts import WriteTimeoutIoPipelineHandler
from ..lite.check import check
from .codecs import RpcEnvelopeCodec
from .codecs import RpcEnvelopeCodecIoPipelineHandler
from .configs import RpcConfig
from .framing import RpcLengthPrefixedFramingIoPipelineHandler
from .keepalive import RpcKeepaliveIoPipelineHandler
from .session import RpcSessionIoPipelineHandler


##


def rpc_build_pipeline_spec(
        config: RpcConfig = RpcConfig.DEFAULT,
        *,
        outermost_handlers: ta.Sequence[IoPipelineHandler] = (),
        transport_handlers: ta.Sequence[IoPipelineHandler] = (),
        innermost_handlers: ta.Sequence[IoPipelineHandler] = (),

        framing_handler: ta.Optional[IoPipelineHandler] = None,
        envelope_codec: ta.Optional[RpcEnvelopeCodec] = None,
        envelope_codec_handler: ta.Optional[IoPipelineHandler] = None,
        handshake_handler: ta.Optional[IoPipelineHandler] = None,
        between_handlers: ta.Sequence[IoPipelineHandler] = (),
        session_handler: ta.Optional[RpcSessionIoPipelineHandler] = None,

        without_flow: bool = False,

        raise_immediately: bool = False,

        metadata: ta.Sequence[IoPipelineMetadata] = (),
        services: ta.Sequence[IoPipelineService] = (),
) -> IoPipeline.Spec:
    """
    Assemble the full pipeline for one rpc connection, outermost (transport side) first.

    The session handler is innermost so that everything a connection enqueues reaches it untouched and everything it
    emits reaches the connection untouched. Framing and the envelope codec sit outside it; the optional handshake,
    keepalive, and idle handlers, and any `between_handlers`, sit between codec and session so they see complete
    envelopes, which makes a slow trickle of bytes that never completes an envelope count as idle. The handshake sits
    nearest the codec, so nothing - keepalive pings included - crosses before the greetings have.

    Optional handlers are passed in as instances rather than switched on by flags, so that this module imports none of
    them and an amalgam carries only those its callers construct: `transport_handlers` sit just inside the outbound
    buffering, where a TLS handler goes (`SslIoPipelineHandler`), and `outermost_handlers` outside everything, where a
    `LoggingIoPipelineHandler` goes.
    """

    if without_flow:
        check.arg(config.inflight_limit_policy != 'pause', "the 'pause' policy requires flow control")

    if framing_handler is None:
        framing_handler = RpcLengthPrefixedFramingIoPipelineHandler(max_frame_bytes=config.max_frame_bytes)

    if envelope_codec_handler is None:
        envelope_codec_handler = RpcEnvelopeCodecIoPipelineHandler(
            envelope_codec,
            max_frame_bytes=config.max_frame_bytes,
        )
    else:
        check.none(envelope_codec, 'envelope_codec is ignored when envelope_codec_handler is given')

    if session_handler is None:
        session_handler = RpcSessionIoPipelineHandler(config)

    keepalive_handlers: ta.List[IoPipelineHandler] = []
    if (ki := config.keepalive_interval_s) is not None:
        keepalive_handlers.append(RpcKeepaliveIoPipelineHandler(
            interval_s=ki,
            timeout_s=check.not_none(config.keepalive_timeout_s),
        ))

    return IoPipeline.Spec(
        [
            *outermost_handlers,

            *([OutboundBytesBufferIoPipelineHandler()] if not without_flow else []),

            *transport_handlers,

            *([WriteTimeoutIoPipelineHandler(t)] if (t := config.write_timeout_s) is not None else []),

            framing_handler,

            envelope_codec_handler,

            *([handshake_handler] if handshake_handler is not None else []),

            *keepalive_handlers,

            *([IdleStateIoPipelineHandler(all_idle_timeout_s=t)] if (t := config.idle_timeout_s) is not None else []),

            *between_handlers,

            session_handler,

            *innermost_handlers,
        ],

        config=IoPipeline.Config.DEFAULT.update(
            raise_immediately=raise_immediately,
        ),

        metadata=metadata,

        services=[
            *([StubIoPipelineFlowService(auto_read=config.inflight_limit_policy != 'pause')] if not without_flow else []),  # noqa
            *services,
        ],
    )
