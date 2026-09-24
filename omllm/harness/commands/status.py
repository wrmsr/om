from omcore.argparse import all as argparse

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
    ) -> None:
        super().__init__()

        self._session_id = session_id

    async def _run_args(self, ctx: CommandContext, args: argparse.Namespace) -> None:
        await ctx.print(ui.Text.join('\n', [
            *([f'Session Id: {self._session_id.v}'] if self._session_id is not None else []),
        ]))
