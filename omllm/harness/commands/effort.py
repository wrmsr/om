from omcore import dataclasses as dc
from omcore.argparse import all as ap

from ... import agent as agn
from ... import llm
from .base import CommandContext
from .classes import CommandClass


##


class EffortCommand(CommandClass):
    def __init__(self, *, agent: agn.Agent, backends: agn.BackendManager) -> None:
        super().__init__()

        self._agent = agent
        self._backends = backends

    @property
    def description(self) -> str:
        return 'Shows or sets reasoning effort for subsequent prompts; default clears the override.'

    def _configure_parser(self, parser: ap.ArgumentParser) -> None:
        super()._configure_parser(parser)

        parser.add_argument('level', nargs='?', choices=['default', *llm.ReasoningEffort])

    async def _run_args(self, ctx: CommandContext, args: ap.Namespace) -> None:
        model = self._backends.get_backend(
            llm.ImmediateBackend, self._agent.state.model,  # type: ignore[type-abstract]
        ).model
        with_tools = bool(self._agent.state.context.tools)

        if args.level is not None:
            effort = None if args.level == 'default' else llm.ReasoningEffort(args.level)
            try:
                llm.validate_reasoning_effort(model, effort, with_tools=with_tools)

                def update(state: agn.State) -> agn.State:
                    config = state.turn_config or agn.TurnConfig()
                    return dc.replace(state, turn_config=dc.replace(
                        config,
                        llm_options=dc.replace(config.llm_options or llm.Options(), reasoning_effort=effort),
                    ))

                await self._agent.update_state_exclusively(update)

            except (ValueError, agn.AgentBusyError) as e:
                await ctx.print(f'Cannot change effort: {e if isinstance(e, ValueError) else "the agent is busy"}')
                return

        options = llm.Options().merge(
            model.default_options,
            (self._agent.state.turn_config or agn.TurnConfig()).llm_options,
        )
        supported = llm.supported_reasoning_efforts(model, with_tools=with_tools)
        levels = ', '.join(e.value for e in llm.ReasoningEffort if e in supported)
        await ctx.print('\n'.join([
            f'Effort: {options.reasoning_effort or "provider default"}',
            f'Supported: {levels or "unavailable"}',
        ]))
