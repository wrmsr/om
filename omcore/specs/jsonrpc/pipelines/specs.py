import typing as ta

from .... import check
from ....io.pipelines import all as ipl
from .codecs import JsonrpcCodecHandler
from .configs import JsonrpcPipelineConfig
from .framing import ContentLengthJsonrpcFramingHandler
from .framing import JsonrpcFramingHandler
from .framing import NdjsonJsonrpcFramingHandler
from .sessions import JsonrpcSessionHandler


##


def build_jsonrpc_framing_handler(config: JsonrpcPipelineConfig) -> JsonrpcFramingHandler:
    if config.framing == 'ndjson':
        return NdjsonJsonrpcFramingHandler(max_frame_bytes=config.max_frame_bytes)
    elif config.framing == 'content-length':
        return ContentLengthJsonrpcFramingHandler(max_frame_bytes=config.max_frame_bytes)
    else:
        raise ValueError(config.framing)


def build_jsonrpc_pipeline_spec(
        config: JsonrpcPipelineConfig = JsonrpcPipelineConfig.DEFAULT,
        *,
        outermost_handlers: ta.Sequence[ipl.Handler] = (),
        innermost_handlers: ta.Sequence[ipl.Handler] = (),

        framing_handler: JsonrpcFramingHandler | None = None,
        session_handler: JsonrpcSessionHandler | None = None,

        with_logging: bool = False,

        ssl_kwargs: ta.Mapping[str, ta.Any] | None = None,

        without_flow: bool = False,

        raise_immediately: bool = False,

        metadata: ta.Sequence[ipl.Metadata] = (),
        services: ta.Sequence[ipl.Service] = (),
) -> ipl.Pipeline.Spec:
    """
    Assemble the full pipeline for one JSON-RPC connection, outermost (transport side) first.

    The session handler is innermost so that everything a host enqueues reaches it untouched and everything it emits
    reaches the host untouched. Byte-level and message-level framing and codec sit outside it; the idle handler sits
    between codec and session so that idleness is measured in complete messages, which makes a slow trickle of bytes
    that never completes a message count as idle.
    """

    if without_flow:
        check.arg(config.inflight_limit_policy != 'pause', "the 'pause' policy requires flow control")

    if framing_handler is None:
        framing_handler = build_jsonrpc_framing_handler(config)

    if session_handler is None:
        session_handler = JsonrpcSessionHandler(config)

    return ipl.Pipeline.Spec(
        [
            *outermost_handlers,

            *([ipl.LoggingHandler()] if with_logging else []),

            *([ipl.OutboundBytesBufferHandler()] if not without_flow else []),

            *([ipl.SslHandler(**ssl_kwargs)] if ssl_kwargs is not None else []),

            *([ipl.WriteTimeoutHandler(t)] if (t := config.write_timeout_s) is not None else []),

            framing_handler,

            JsonrpcCodecHandler(
                max_frame_bytes=config.max_frame_bytes,
                parse_options=config.parse_options,
            ),

            *([ipl.IdleStateHandler(all_idle_timeout_s=t)] if (t := config.idle_timeout_s) is not None else []),

            session_handler,

            *innermost_handlers,
        ],

        config=ipl.Pipeline.Config.DEFAULT.update(
            raise_immediately=raise_immediately,
        ),

        metadata=metadata,

        services=[
            *([ipl.StubFlowService(auto_read=config.inflight_limit_policy != 'pause')] if not without_flow else []),
            *services,
        ],
    )
