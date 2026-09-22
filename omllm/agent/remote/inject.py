from omcore import inject as inj

from ...core.processes.managers.types import ProcessManager
from ..fs.ops import FsOps
from .client import RemoteAgentClient
from .client import RemoteFsOps
from .client import RemoteProcessManager
from .docker import DockerContainerIdt
from .docker import DockerRemoteAgentConfig
from .docker import DockerRemoteAgentConnection


##


def _provide_remote_agent_client(connection: DockerRemoteAgentConnection) -> RemoteAgentClient:
    return connection.client


def _provide_remote_fs(client: RemoteAgentClient) -> RemoteFsOps:
    return client.fs


def _provide_remote_processes(client: RemoteAgentClient) -> RemoteProcessManager:
    return client.processes


def bind_docker_remote_agent(
        container_id: DockerContainerIdt,
        config: DockerRemoteAgentConfig | None = None,
) -> inj.Elements:
    return inj.as_elements(
        inj.bind(container_id),
        inj.bind(config if config is not None else DockerRemoteAgentConfig()),

        inj.bind(
            DockerRemoteAgentConnection,
            singleton=True,
            to_async_fn=inj.make_async_managed_provider(DockerRemoteAgentConnection),
        ),
        inj.bind(RemoteAgentClient, singleton=True, to_fn=_provide_remote_agent_client),

        inj.bind(RemoteFsOps, singleton=True, to_fn=_provide_remote_fs),
        inj.bind(FsOps, to_key=RemoteFsOps),

        inj.bind(RemoteProcessManager, singleton=True, to_fn=_provide_remote_processes),
        inj.bind(ProcessManager, to_key=RemoteProcessManager),
    )
