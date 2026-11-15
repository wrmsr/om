import contextvars
import typing as ta

from omcore import inject as inj
from omcore import lang

from ...agent.tools.inject import ScopedToolInvoker
from ...agent.turns.inject import ScopedTurnRunner


##


class SUBAGENT_TURN_SCOPED(lang.Marker):  # noqa
    pass


_SUBAGENT_TURN_SCOPE_CONTEXT: contextvars.ContextVar = contextvars.ContextVar(
    f'{__name__}._SUBAGENT_TURN_SCOPE_CONTEXT',
)

# A turn scope of the subagent's own. A child injector may not redeclare its ancestor's `TURN_SCOPE`, and the parent's
# opening of it is in any case visible in the task a subagent runs in, so a nested opening would be refused. Each child
# injector registers this scope for itself: the scope's state is per injector, so any number of subagents run at once
# without seeing each other's openings.
SUBAGENT_TURN_SCOPE: ta.Final = inj.DelimitedScope(
    SUBAGENT_TURN_SCOPED,
    context=inj.ContextVarScopeContext(_SUBAGENT_TURN_SCOPE_CONTEXT),
)


def provide_subagent_turn_runner(injector: inj.AsyncInjector) -> ScopedTurnRunner:
    return ScopedTurnRunner(
        injector=injector,
        scope=SUBAGENT_TURN_SCOPE,
    )


##


class SUBAGENT_TOOL_INVOCATION_SCOPED(lang.Marker):  # noqa
    pass


_SUBAGENT_TOOL_INVOCATION_SCOPE_CONTEXT: contextvars.ContextVar = contextvars.ContextVar(
    f'{__name__}._SUBAGENT_TOOL_INVOCATION_SCOPE_CONTEXT',
)

# A tool invocation scope of the subagent's own, for the turn scope's reasons and then some: a subagent runs inside the
# parent's subagent tool call, which is itself an opening of the parent's `TOOL_INVOCATION_SCOPE`. Falling through to
# the parent's invoker would open that scope again, on the parent's injector, in a task which already sees it open.
SUBAGENT_TOOL_INVOCATION_SCOPE: ta.Final = inj.DelimitedScope(
    SUBAGENT_TOOL_INVOCATION_SCOPED,
    context=inj.ContextVarScopeContext(_SUBAGENT_TOOL_INVOCATION_SCOPE_CONTEXT),
)


def provide_subagent_tool_invoker(injector: inj.AsyncInjector) -> ScopedToolInvoker:
    return ScopedToolInvoker(
        injector=injector,
        scope=SUBAGENT_TOOL_INVOCATION_SCOPE,
    )
