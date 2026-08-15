import typing as ta

from omcore import inject as inj
from omcore import lang

from ... import agent as agn
from .config import Config


##


AgentTools = ta.NewType('AgentTools', ta.Sequence[agn.Tool])


@lang.cached_function
def agent_tools() -> inj.ItemsBinderHelper[agn.Tool]:
    return inj.items_binder_helper[agn.Tool](AgentTools)


def bind_agent_tool_class(tool_cls: type[agn.ToolClass]) -> inj.Elements:
    return agent_tools().bind_item(to_fn=inj.target(o=tool_cls)(lambda o: o.tool()))


##


def bind_tools(config: Config) -> inj.Elements:
    lst: list[inj.Elemental] = []

    if config.eval:
        lst.extend([
            inj.bind(agn.QuickjsTool, singleton=True),
            bind_agent_tool_class(agn.QuickjsTool),
        ])

    if config.exec:
        lst.extend([
            inj.bind(agn.LocalExecOps, singleton=True),
            inj.bind(agn.ExecOps, to_key=agn.LocalExecOps),

            inj.bind(agn.BashTool, singleton=True),
            bind_agent_tool_class(agn.BashTool),
        ])

    if config.fs:
        lst.extend([
            inj.bind(agn.LocalFsOps, singleton=True),
            inj.bind(agn.FsOps, to_key=agn.LocalFsOps),

            inj.bind(agn.EditTool, singleton=True),
            bind_agent_tool_class(agn.EditTool),

            inj.bind(agn.LsTool, singleton=True),
            bind_agent_tool_class(agn.LsTool),

            inj.bind(agn.ReadTool, singleton=True),
            bind_agent_tool_class(agn.ReadTool),

            inj.bind(agn.WriteTool, singleton=True),
            bind_agent_tool_class(agn.WriteTool),
        ])

    if config.exec and config.fs:
        lst.extend([
            inj.bind(agn.RipgrepTool, singleton=True),
            bind_agent_tool_class(agn.RipgrepTool),
        ])

    if config.web:
        lst.extend([
            inj.bind(agn.WebFetchTool, singleton=True),
            bind_agent_tool_class(agn.WebFetchTool),

            inj.bind(agn.WebSearchTool, singleton=True),
            bind_agent_tool_class(agn.WebSearchTool),
        ])

    lst.extend([
        agent_tools().bind_items_provider(singleton=True),

        inj.bind(
            agn.ToolSet,
            to_fn=inj.target(ats=AgentTools)(lambda ats: agn.ToolSet(ats)),
            singleton=True,
        ),
    ])

    return inj.as_elements(*lst)
