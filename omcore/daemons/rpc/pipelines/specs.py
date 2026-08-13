import uuid

from ....io.pipelines.core import IoPipeline
from ....io.pipelines.flow.stub import StubIoPipelineFlowService
from .codecs import RpcFrameCodecIoPipelineHandler
from .codecs import RpcJsonCodecIoPipelineHandler
from .sessions import RpcClientSessionIoPipelineHandler
from .sessions import RpcServerSessionIoPipelineHandler


##


def rpc_client_pipeline_spec(
        *,
        protocol_version: int,
        max_frame_bytes: int,
) -> IoPipeline.Spec:
    return IoPipeline.Spec(
        handlers=[
            RpcFrameCodecIoPipelineHandler(max_frame_bytes),
            RpcJsonCodecIoPipelineHandler(),
            RpcClientSessionIoPipelineHandler(protocol_version),
        ],
        services=[StubIoPipelineFlowService()],
    )


def rpc_server_pipeline_spec(
        *,
        protocol_version: int,
        instance_id: uuid.UUID,
        max_frame_bytes: int,
) -> IoPipeline.Spec:
    return IoPipeline.Spec(
        handlers=[
            RpcFrameCodecIoPipelineHandler(max_frame_bytes),
            RpcJsonCodecIoPipelineHandler(),
            RpcServerSessionIoPipelineHandler(
                protocol_version=protocol_version,
                instance_id=instance_id,
            ),
        ],
        services=[StubIoPipelineFlowService()],
    )
