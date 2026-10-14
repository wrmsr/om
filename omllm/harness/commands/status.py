from omcore.argparse import all as argparse

from ... import agent as agn
from ...core import ui
from ..sessions.types import SessionId
from .base import CommandContext
from .classes import CommandClass


##


class StatusCommand(CommandClass):
    def __init__(
            self,
            *,
            session_id: SessionId | None = None,
            agent: agn.Agent,
    ) -> None:
        super().__init__()

        self._session_id = session_id
        self._agent = agent

    async def _run_args(self, ctx: CommandContext, args: argparse.Namespace) -> None:
        lines: list[ui.CanText] = []

        if (session_id := self._session_id) is not None:
            lines.append(f'Session Id: {session_id.v}')

        if (model := self._agent.state.model) is not None:
            if (model_key := model.key) is not None:
                lines.append(f'Model: {model_key.joined}')

        await ctx.print(ui.Text.join('\n', lines))
