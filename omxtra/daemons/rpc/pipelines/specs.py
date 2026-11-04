"""
The daemons rpc pipelines, assembled from `omcore.rpc` legos: its framing (the same four-byte big-endian length frames),
the daemons dialect codec, a hello handshake, and - server side - a close after the one request a connection carries.
"""
import typing as ta
import uuid

from omcore import dataclasses as dc
from omcore.io.pipelines import all as ipl
from omcore.rpc.closing import RpcCloseAfterRequestsIoPipelineHandler
from omcore.rpc.configs import RpcConfig
from omcore.rpc.handshake import RpcHandshakeIoPipelineHandler
from omcore.rpc.specs import rpc_build_pipeline_spec

from ..protocol import RpcProtocolError
from .codecs import DAEMONS_RPC_ENVELOPE_CODEC
from .codecs import rpc_client_hello
from .codecs import rpc_hello_instance_id
from .codecs import rpc_hello_version
from .codecs import rpc_server_hello


##


@dc.dataclass(frozen=True)
class RpcPipeline:
    config: RpcConfig
    spec: ipl.Pipeline.Spec
    handshake: RpcHandshakeIoPipelineHandler


def rpc_client_config(
        *,
        max_frame_bytes: int,
        io_timeout_s: float | None,
) -> RpcConfig:
    return RpcConfig(
        max_frame_bytes=max_frame_bytes,

        # The client's io timeout bounds the request, the handshake waited on before it, and every flush.
        default_request_timeout_s=io_timeout_s,
        write_timeout_s=io_timeout_s,

        # The dialect has no cancel: an abandoned request is only forgotten.
        cancel_abandoned_requests=False,
        default_ping_timeout_s=None,

        close_drain_timeout_s=io_timeout_s,
    )


def rpc_server_config(
        *,
        max_frame_bytes: int,
        connection_timeout_s: float | None,
) -> RpcConfig:
    return RpcConfig(
        max_frame_bytes=max_frame_bytes,

        # A connection with nothing in flight for this long - a client which connects and says nothing, say - is
        # closed. A request being handled is never timed out.
        idle_timeout_s=connection_timeout_s,
        write_timeout_s=connection_timeout_s,

        cancel_abandoned_requests=False,
        default_ping_timeout_s=None,
    )


def rpc_client_pipeline(
        *,
        protocol_version: int,
        max_frame_bytes: int,
        io_timeout_s: float | None = None,
) -> RpcPipeline:
    def validate(hello: ta.Mapping[str, ta.Any]) -> None:
        version = rpc_hello_version(hello)
        if version != protocol_version:
            raise RpcProtocolError(
                f'RPC protocol version mismatch: client={protocol_version}, server={version!r}',
            )
        rpc_hello_instance_id(hello)

    config = rpc_client_config(max_frame_bytes=max_frame_bytes, io_timeout_s=io_timeout_s)
    handshake = RpcHandshakeIoPipelineHandler(
        rpc_client_hello(protocol_version),
        initiate=True,
        validate=validate,
    )
    return RpcPipeline(
        config,
        rpc_build_pipeline_spec(
            config,
            envelope_codec=DAEMONS_RPC_ENVELOPE_CODEC,
            handshake_handler=handshake,
        ),
        handshake,
    )


def rpc_server_pipeline(
        *,
        protocol_version: int,
        instance_id: uuid.UUID,
        max_frame_bytes: int,
        connection_timeout_s: float | None = None,
) -> RpcPipeline:
    def validate(hello: ta.Mapping[str, ta.Any]) -> None:
        version = rpc_hello_version(hello)
        if version != protocol_version:
            raise RpcProtocolError(
                f'RPC protocol version mismatch: client={version!r}, server={protocol_version}',
            )

    config = rpc_server_config(max_frame_bytes=max_frame_bytes, connection_timeout_s=connection_timeout_s)
    handshake = RpcHandshakeIoPipelineHandler(
        rpc_server_hello(protocol_version, instance_id),
        initiate=False,
        validate=validate,
    )
    return RpcPipeline(
        config,
        rpc_build_pipeline_spec(
            config,
            envelope_codec=DAEMONS_RPC_ENVELOPE_CODEC,
            handshake_handler=handshake,
            between_handlers=[RpcCloseAfterRequestsIoPipelineHandler()],
        ),
        handshake,
    )
