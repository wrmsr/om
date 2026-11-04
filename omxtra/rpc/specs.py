# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
import typing as ta

from omcore.io.pipelines.bytes.buffers import OutboundBytesBufferIoPipelineHandler
from omcore.io.pipelines.core import IoPipeline
from omcore.io.pipelines.core import IoPipelineHandler
from omcore.io.pipelines.core import IoPipelineMetadata
from omcore.io.pipelines.core import IoPipelineService
from omcore.io.pipelines.flow.stub import StubIoPipelineFlowService
from omcore.io.pipelines.handlers.logs import LoggingIoPipelineHandler
from omcore.io.pipelines.sched.timeouts import IdleStateIoPipelineHandler
from omcore.io.pipelines.sched.timeouts import WriteTimeoutIoPipelineHandler
from omcore.io.pipelines.ssl.handlers import SslIoPipelineHandler
from omcore.lite.check import check

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
        innermost_handlers: ta.Sequence[IoPipelineHandler] = (),

        framing_handler: ta.Optional[IoPipelineHandler] = None,
        envelope_codec: ta.Optional[RpcEnvelopeCodec] = None,
        envelope_codec_handler: ta.Optional[IoPipelineHandler] = None,
        between_handlers: ta.Sequence[IoPipelineHandler] = (),
        session_handler: ta.Optional[RpcSessionIoPipelineHandler] = None,

        with_logging: bool = False,

        ssl_kwargs: ta.Optional[ta.Mapping[str, ta.Any]] = None,

        without_flow: bool = False,

        raise_immediately: bool = False,

        metadata: ta.Sequence[IoPipelineMetadata] = (),
        services: ta.Sequence[IoPipelineService] = (),
) -> IoPipeline.Spec:
    """
    Assemble the full pipeline for one rpc connection, outermost (transport side) first.

    The session handler is innermost so that everything a connection enqueues reaches it untouched and everything it
    emits reaches the connection untouched. Framing and the envelope codec sit outside it; the optional keepalive and
    idle handlers, and any `between_handlers`, sit between codec and session so they see complete envelopes, which
    makes a slow trickle of bytes that never completes an envelope count as idle.
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

            *([LoggingIoPipelineHandler()] if with_logging else []),

            *([OutboundBytesBufferIoPipelineHandler()] if not without_flow else []),

            *([SslIoPipelineHandler(**ssl_kwargs)] if ssl_kwargs is not None else []),

            *([WriteTimeoutIoPipelineHandler(t)] if (t := config.write_timeout_s) is not None else []),

            framing_handler,

            envelope_codec_handler,

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
