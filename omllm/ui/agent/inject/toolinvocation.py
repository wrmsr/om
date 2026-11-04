import contextvars
import typing as ta

from omcore import inject as inj
from omcore import lang

from .... import agent as agn
from ..config import AgentConfig


##


class TOOL_INVOCATION_SCOPED(lang.Marker):  # noqa
    pass


_TOOL_INVOCATION_SCOPE_CONTEXT: contextvars.ContextVar = contextvars.ContextVar(
    f'{__name__}._TOOL_INVOCATION_SCOPE_CONTEXT',
)

# Per context, as the turn scope is, and for a more pressing reason: a message's tool calls run concurrently, each in a
# task of its own, and each opens the scope for itself. Those tasks are spawned inside the turn's opening and inherit
# it, so what is bound here may depend on the turn's bindings as well as on the call's seeds.
TOOL_INVOCATION_SCOPE: ta.Final = inj.DelimitedScope(
    TOOL_INVOCATION_SCOPED,
    context=inj.ContextVarScopeContext(_TOOL_INVOCATION_SCOPE_CONTEXT),
)


#


class ScopedToolInvoker(agn.ToolInvoker):
    """
    The turn's seam, one level down: each tool call is invoked in an opening of the agent's tool invocation scope,
    seeded with the tool and its context, so what an invocation is built from may be bound per tool call. Which scope
    is the agent's goes as it does for `ScopedTurnRunner`: the root agent's is `TOOL_INVOCATION_SCOPE`, and an agent
    scope of its own - a subagent's - has one of its own.
    """

    def __init__(
            self,
            *,
            injector: inj.AsyncInjector,
            scope: inj.DelimitedScope | None = None,
    ) -> None:
        super().__init__()

        self._injector = injector
        self._scope = scope if scope is not None else TOOL_INVOCATION_SCOPE

    async def invoke_tool(self, tool: agn.Tool, ctx: agn.ToolContext) -> agn.ToolResult:
        async with inj.async_enter_scope(
                self._injector,
                self._scope,
                {
                    inj.as_key(agn.Tool): tool,
                    inj.as_key(agn.ToolContext): ctx,
                },
        ):
            invoker = await self._injector[agn.DirectToolInvoker]

            return await invoker.invoke_tool(tool, ctx)


##


def bind_tool_invocation(config: AgentConfig) -> inj.Elements:
    lst: list[inj.Elemental] = []

    #

    lst.extend([
        inj.bind_scope(TOOL_INVOCATION_SCOPE),
        inj.bind_scope_seed(agn.Tool, TOOL_INVOCATION_SCOPE),
        inj.bind_scope_seed(agn.ToolContext, TOOL_INVOCATION_SCOPE),

        inj.bind(ScopedToolInvoker, singleton=True),
        inj.bind(agn.ToolInvoker, to_key=ScopedToolInvoker),

        inj.bind(agn.DirectToolInvoker, in_=TOOL_INVOCATION_SCOPE),
    ])

    #

    return inj.as_elements(*lst)
