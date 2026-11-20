import contextlib
import typing as ta

from omcore import inject as inj

from ... import agent as agn
from ... import llm
from ..agent.config import AgentConfig
from ..agent.inject.inject import bind_agent
from ..agent.setup import AgentSetup
from ..backends.config import BackendsConfig
from ..backends.inject import bind_backends


##


class _DenyPermissionAsker(agn.PermissionAsker):
    async def ask(self, request: agn.PermissionRequest, rule: agn.PermissionRule) -> agn.DecidedPermissionState:
        return agn.PermissionState.DENY


@contextlib.asynccontextmanager
async def eval_agent(
        *,
        cwd: str,
        model: str,
        script: llm.BackendScript | None,
        container: agn.DockerContainerId | None = None,
        docker: str = 'docker',
        remote_client: agn.RemoteAgentClient | None = None,
) -> ta.AsyncIterator[tuple[agn.Agent, agn.PermissionsManager]]:
    agent_bindings: inj.Elemental = bind_agent(AgentConfig(
        cwd=cwd,
        container=container.render() if container is not None else None,
        in_memory=True,
        exec=True,
        fs=True,
    ), remote_client=remote_client)
    if container is not None:
        agent_bindings = inj.override(agent_bindings, inj.bind(agn.DockerRemoteAgentConfig(docker=docker)))

    backend_bindings: inj.Elemental = bind_backends(BackendsConfig(model=model))
    if script is not None:
        backend = llm.ScriptedImmediateBackend(llm.Model(
            key=llm.ModelKey('scripted', 'scripted'),
            backend='scripted',
        ), script)
        backend_bindings = inj.override(backend_bindings, inj.bind(
            agn.BackendManager,
            to_const=agn.DictBackendManager.of(backend),
        ))

    async with inj.create_asyncio_managed_injector(
        agent_bindings,
        backend_bindings,
        inj.bind(agn.PermissionAsker, to_const=_DenyPermissionAsker()),
    ) as injector:
        agent = await injector[agn.Agent]
        await (await injector[AgentSetup]).run()
        yield agent, await injector[agn.PermissionsManager]
