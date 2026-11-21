from omcore.argparse import all as argparse

from ... import agent as agn
from ...core import ui
from .argparse import ArgparseCommand
from .base import CommandContext


##


class StatusCommand(ArgparseCommand):
    def __init__(
            self,
            *,
            session_id: agn.SessionId | None = None,
            agent: agn.Agent,
    ) -> None:
        super().__init__()

        self._session_id = session_id
        self._agent = agent

    async def _run_args(self, ctx: CommandContext, args: argparse.Namespace) -> None:
        lines: list[ui.CanText] = []
        state = self._agent.state

        if (session_id := self._session_id) is not None:
            lines.append(f'Session Id: {session_id.v}')

        if (model := state.model) is not None:
            if (model_key := model.key) is not None:
                lines.append(f'Model: {model_key.joined}')

        if (
                (turn_config := state.turn_config) is not None and
                (llm_options := turn_config.llm_options) is not None and
                (effort := llm_options.reasoning_effort) is not None
        ):
            lines.append(f'Effort: {effort}')

        if (usage := state.context.usage) is not None:
            parts = [
                f'in {usage.input:,}',
                *(
                    [f'cached {usage.cache_read:,}']
                    if usage.cache_read else []
                ),
                *(
                    [f'cache write {usage.cache_write:,}']
                    if usage.cache_write else []
                ),
                f'out {usage.output:,}',
                *(
                    [f'reasoning {usage.reasoning:,}']
                    if usage.reasoning else []
                ),
            ]
            lines.append(f'Usage: {", ".join(parts)}')
            if usage.cost is not None:
                cost_s = f'${usage.cost:.4f}' if 0. < abs(usage.cost) < .01 else f'${usage.cost:.2f}'
                lines.append(f'Cost: {cost_s}')

        if (budget := state.context.context_budget) is not None and budget.input is not None:
            est = '~' if budget.is_estimated else ''
            lines.append(f'Context: {est}{budget.input:,} / {budget.input_limit:,}')

        await ctx.print(ui.Text.join('\n', lines))
