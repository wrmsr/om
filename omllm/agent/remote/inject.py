from omcore import inject as inj

from ...core.processes.inject import bind_root_process_scope
from ...core.processes.managers.types import ProcessManager
from ...core.processes.remote.client import RemoteProcessManager
from ..environment.ops import EnvironmentOps
from ..environment.remote.client import RemoteEnvironmentOps
from ..fs.ops import FsOps
from ..fs.remote.client import RemoteFsOps
from .client import RemoteAgentClient
from .docker import DockerContainerIdt
from .docker import DockerRemoteAgentConfig
from .docker import DockerRemoteAgentConnection


##


def _provide_remote_environment(client: RemoteAgentClient) -> RemoteEnvironmentOps:
    return client.environment


def _provide_remote_fs(client: RemoteAgentClient) -> RemoteFsOps:
    return client.fs


def _provide_remote_processes(client: RemoteAgentClient) -> RemoteProcessManager:
    return client.processes


def bind_remote_agent_ops() -> inj.Elements:
    """
    The ordinary agent interfaces over a bound `RemoteAgentClient`, whatever stood the connection up: the environment,
    the filesystem, and processes - with the root process scope the ui hands to tools.
    """

    return inj.as_elements(
        inj.bind(RemoteEnvironmentOps, singleton=True, to_fn=_provide_remote_environment),
        inj.bind(EnvironmentOps, to_key=RemoteEnvironmentOps),

        inj.bind(RemoteFsOps, singleton=True, to_fn=_provide_remote_fs),
        inj.bind(FsOps, to_key=RemoteFsOps),

        inj.bind(RemoteProcessManager, singleton=True, to_fn=_provide_remote_processes),
        inj.bind(ProcessManager, to_key=RemoteProcessManager),
        bind_root_process_scope(),
    )


##


def _provide_docker_remote_agent_client(connection: DockerRemoteAgentConnection) -> RemoteAgentClient:
    return connection.client


def bind_docker_remote_agent(
        container_id: DockerContainerIdt,
        config: DockerRemoteAgentConfig | None = None,
) -> inj.Elements:
    """A remote agent in a docker container: the connection, and the agent interfaces over it."""

    return inj.as_elements(
        inj.bind(container_id),
        inj.bind(config if config is not None else DockerRemoteAgentConfig()),

        inj.bind(
            DockerRemoteAgentConnection,
            singleton=True,
            to_async_fn=inj.make_async_managed_provider(DockerRemoteAgentConnection),
        ),
        inj.bind(RemoteAgentClient, singleton=True, to_fn=_provide_docker_remote_agent_client),

        bind_remote_agent_ops(),
    )
