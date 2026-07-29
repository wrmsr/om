import enum
import shlex
import typing as ta

from omcore import collections as col

from ...core.ui import UiTextDisplayer
from .base import Command
from .base import Commands


##


class RunCommandResult(enum.StrEnum):
    SUCCESS = 'success'
    FAILURE = 'failure'


class CommandsManager:
    def __init__(
            self,
            *,
            commands: Commands,
            ui_text_displayer: UiTextDisplayer,
    ) -> None:
        super().__init__()

        self._commands = commands
        self._ui_text_displayer = ui_text_displayer

        self._commands_by_name = col.make_map((
            (c.name, c) for c in commands
        ), strict=True)

    def get_commands(self) -> ta.Mapping[str, Command]:
        return self._commands_by_name

    async def run_command_text(self, text: str) -> RunCommandResult:
        try:
            parts = shlex.split(text)
        except ValueError as e:
            await self._ui_text_displayer.display_ui_text(f'Invalid command syntax: {e}')
            return RunCommandResult.FAILURE

        if not parts:
            return RunCommandResult.FAILURE

        cmd = parts[0].lower()
        argv = parts[1:]

        command = self._commands_by_name.get(cmd)
        if not command:
            await self._ui_text_displayer.display_ui_text(f'Unknown command: {cmd}')
            return RunCommandResult.FAILURE

        ctx = Command.Context(
            print=self._ui_text_displayer.display_ui_text,
        )

        await command.run(ctx, argv)

        return RunCommandResult.SUCCESS
