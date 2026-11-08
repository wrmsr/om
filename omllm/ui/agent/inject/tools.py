import typing as ta

from omcore import inject as inj
from omcore import lang
from omcore.asyncs.asynclite import all as asl

from .... import agent as agn
from ....agent.remote.inject import bind_docker_remote_agent
from ....core import processes
from ...types import RequestedCwd
from ..config import AgentConfig


##


AgentTools = ta.NewType('AgentTools', ta.Sequence[agn.Tool])


@lang.cached_function
def agent_tools() -> inj.ItemsBinderHelper[agn.Tool]:
    return inj.items_binder_helper[agn.Tool](AgentTools)


def bind_agent_tool_class(tool_cls: type[agn.ToolClass]) -> inj.Elements:
    return agent_tools().bind_item(to_fn=inj.target(o=tool_cls)(lambda o: o.tool()))


#


AgentToolSets = ta.NewType('AgentToolSets', ta.Sequence[agn.ToolSet])


@lang.cached_function
def agent_tool_sets() -> inj.ItemsBinderHelper[agn.ToolSet]:
    """Tool sets discovered at provisioning time, alongside individually bound tools."""

    return inj.items_binder_helper[agn.ToolSet](AgentToolSets)


def _provide_tool_set(tools: AgentTools, tool_sets: AgentToolSets) -> agn.ToolSet:
    return agn.ToolSet([*tools, *(t for ts in tool_sets for t in ts)])


##


class _EnvironmentInfoGetter:
    def __init__(
            self,
            *,
            ops: agn.EnvironmentOps,
            locks: asl.Locks,
            requested_cwd: RequestedCwd | None = None,
    ) -> None:
        super().__init__()

        self._ops = ops
        self._requested_cwd = requested_cwd
        self._lock = locks.make_lock()
        self._info: agn.EnvironmentInfo | None = None

    async def __call__(self) -> agn.EnvironmentInfo:
        if (info := self._info) is not None:
            return info

        async with self._lock:
            if (info := self._info) is not None:
                return info

            info = await self._ops.inspect_environment(
                cwd=self._requested_cwd.v if self._requested_cwd is not None else None,
            )

            self._info = info
            return info


##


def bind_tool_infrastructure(config: AgentConfig) -> inj.Elements:
    """
    What tools stand on, bound once for the whole app: the environment they work in, what they run processes on,
    and the ops they share. An agent scope - the root agent's today, a subagent's - binds its own tool classes over
    these.
    """

    lst: list[inj.Elemental] = []

    # An environment and a process manager are bound either way, whatever tools the agent is given: the agent is told
    # where it is regardless, and the user's own shell runs on the manager too.
    if config.container is not None:
        lst.extend([
            bind_docker_remote_agent(agn.DockerContainerIdt(config.container)),
        ])
    else:
        lst.extend([
            inj.bind(agn.LocalEnvironmentOps, singleton=True),
            inj.bind(agn.EnvironmentOps, to_key=agn.LocalEnvironmentOps),

            processes.bind_process_manager(),
        ])

    lst.extend([
        inj.bind(_EnvironmentInfoGetter, singleton=True),
        inj.bind(agn.EnvironmentInfoGetter, to_key=_EnvironmentInfoGetter),
    ])

    # As asked for, unresolved: the environment resolves it at the agent's setup, not here.
    if config.cwd is not None:
        lst.append(inj.bind(RequestedCwd(config.cwd)))

    # Tools are given a process scope, not the root one in particular: the root agent's is the root scope, and an agent
    # scope beneath it binds a child of its parent's over this.
    lst.append(inj.bind(processes.ProcessScope, to_key=processes.RootProcessScope))

    if config.exec:
        lst.extend([
            inj.bind(agn.ProcessesExecOps, singleton=True),
            inj.bind(agn.ExecOps, to_key=agn.ProcessesExecOps),
        ])

    if config.fs and config.container is None:
        lst.extend([
            inj.bind(agn.LocalFsOps, singleton=True),
            inj.bind(agn.FsOps, to_key=agn.LocalFsOps),
        ])

    return inj.as_elements(*lst)


##


def _provide_unsandboxed_ripgrep_tool(
        permissions: agn.PermissionDecider,
        exec: agn.ExecOps,  # noqa
        fs: agn.FsOps,
) -> agn.RipgrepTool:
    # The platform sandbox confines a local `rg` by its host path. Against a container the process runs remotely, where
    # neither the host's sandbox nor the host's `rg` applies, so it is left target-relative and unconfined.
    return agn.RipgrepTool(
        permissions=permissions,
        exec=exec,
        fs=fs,
        sandbox=False,
    )


def bind_tool_classes(config: AgentConfig) -> inj.Elements:
    """
    The tool classes the config calls for, as singletons of the injector this is bound in, each contributed to that
    injector's `AgentTools`. Bound per agent scope: every agent gets instances of its own over the shared
    infrastructure, and an items collection of its own to find them in.
    """

    lst: list[inj.Elemental] = []

    if config.eval:
        lst.extend([
            inj.bind(agn.QuickjsTool, singleton=True),
            bind_agent_tool_class(agn.QuickjsTool),
        ])

    if config.exec:
        lst.extend([
            inj.bind(agn.BashTool, singleton=True),
            bind_agent_tool_class(agn.BashTool),

            inj.bind(agn.ProcessSpawnTool, singleton=True),
            bind_agent_tool_class(agn.ProcessSpawnTool),

            inj.bind(agn.ProcessReadTool, singleton=True),
            bind_agent_tool_class(agn.ProcessReadTool),

            inj.bind(agn.ProcessWriteTool, singleton=True),
            bind_agent_tool_class(agn.ProcessWriteTool),

            inj.bind(agn.ProcessKillTool, singleton=True),
            bind_agent_tool_class(agn.ProcessKillTool),

            inj.bind(agn.ProcessListTool, singleton=True),
            bind_agent_tool_class(agn.ProcessListTool),
        ])

    if config.fs:
        lst.extend([
            inj.bind(agn.EditTool, singleton=True),
            bind_agent_tool_class(agn.EditTool),

            inj.bind(agn.GlobTool, singleton=True),
            bind_agent_tool_class(agn.GlobTool),

            inj.bind(agn.LsTool, singleton=True),
            bind_agent_tool_class(agn.LsTool),

            inj.bind(agn.ReadTool, singleton=True),
            bind_agent_tool_class(agn.ReadTool),

            inj.bind(agn.WriteTool, singleton=True),
            bind_agent_tool_class(agn.WriteTool),
        ])

    if config.exec and config.fs:
        if config.container is not None:
            lst.append(inj.bind(agn.RipgrepTool, singleton=True, to_fn=_provide_unsandboxed_ripgrep_tool))
        else:
            lst.append(inj.bind(agn.RipgrepTool, singleton=True))

        lst.append(bind_agent_tool_class(agn.RipgrepTool))

    if config.web:
        lst.extend([
            inj.bind(agn.WebFetchTool, singleton=True),
            bind_agent_tool_class(agn.WebFetchTool),

            inj.bind(agn.WebSearchTool, singleton=True),
            bind_agent_tool_class(agn.WebSearchTool),
        ])

    lst.extend([
        agent_tools().bind_items_provider(singleton=True),
        agent_tool_sets().bind_items_provider(singleton=True),
    ])

    return inj.as_elements(*lst)


##


def bind_tools(config: AgentConfig) -> inj.Elements:
    return inj.as_elements(
        bind_tool_infrastructure(config),

        bind_tool_classes(config),

        inj.bind(agn.ToolSet, to_fn=_provide_tool_set, singleton=True),
    )
