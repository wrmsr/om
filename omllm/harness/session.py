from omcore import dataclasses as dc
from omcore import lang

from .. import agent as agn
from .commands.manager import CommandsManager


##


@dc.dataclass(frozen=True)
class SessionEntry(lang.Abstract, lang.Sealed):
    pass


##


class Session:
    def __init__(
            self,
            *,
            agent: agn.Agent,
            commands_manager: CommandsManager,
    ) -> None:
        super().__init__()

        self._agent = agent
        self._commands_manager = commands_manager

    async def prompt(
            self,
            input: str,  # noqa
    ) -> None:
        if not input:
            return

        if input.startswith('/'):
            await self._commands_manager.run_command_text(input[1:])
            return

        await self._agent.prompt(input)
