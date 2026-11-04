import contextvars
import typing as ta

from omcore import inject as inj
from omcore import lang

from .... import agent as agn
from ..config import AgentConfig


##


class TURN_SCOPED(lang.Marker):  # noqa
    pass


_TURN_SCOPE_CONTEXT: contextvars.ContextVar = contextvars.ContextVar(f'{__name__}._TURN_SCOPE_CONTEXT')

TURN_SCOPE: ta.Final = inj.DelimitedScope(
    TURN_SCOPED,
    context=inj.ContextVarScopeContext(_TURN_SCOPE_CONTEXT),
)


#


class ScopedTurnRunner(agn.TurnRunner):
    """
    The **sEaM** between an agent and its injector: each turn is run in an opening of the agent's turn scope, seeded
    with its parameters, so what the loop is built from may be bound per turn. Which scope is the agent's: the root
    agent's is `TURN_SCOPE`, and an agent scope of its own - a subagent's - has one of its own.
    """

    def __init__(
            self,
            *,
            injector: inj.AsyncInjector,
            scope: inj.DelimitedScope | None = None,
    ) -> None:
        super().__init__()

        self._injector = injector
        self._scope = scope if scope is not None else TURN_SCOPE

    async def run_turn(self, params: agn.TurnParams) -> agn.TurnResult:
        async with inj.async_enter_scope(
                self._injector,
                self._scope,
                {
                    inj.as_key(agn.TurnParams): params,
                },
        ):
            runner = await self._injector[agn.TurnLoopRunner]

            return await runner.run_turn(params)


##


def bind_turns(config: AgentConfig) -> inj.Elements:
    lst: list[inj.Elemental] = []

    #

    lst.extend([
        inj.bind_scope(TURN_SCOPE),
        inj.bind_scope_seed(agn.TurnParams, TURN_SCOPE),

        inj.bind(ScopedTurnRunner, singleton=True),
        inj.bind(agn.TurnRunner, to_key=ScopedTurnRunner),

        inj.bind(agn.TurnLoop, in_=TURN_SCOPE),
        inj.bind(agn.TurnLoopRunner, in_=TURN_SCOPE),
    ])

    #

    return inj.as_elements(*lst)
