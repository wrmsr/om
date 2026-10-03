import enum
import shlex
import typing as ta

from omcore import collections as col

from ...core import ui
from .base import Command
from .base import CommandContext
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
            text_displayer: ui.TextDisplayer,
    ) -> None:
        super().__init__()

        self._commands = commands
        self._text_displayer = text_displayer

        self._commands_by_name: ta.Mapping[str, Command] = col.make_map((
            (c.name, c) for c in commands
        ), strict=True)

    def get_commands(self) -> ta.Mapping[str, Command]:
        return self._commands_by_name

    def can_run_while_busy(self, text: str) -> bool:
        # Only the command name is needed here. Parsing the arguments remains run_command_text's responsibility, so
        # a malformed steering command still reports its error immediately rather than waiting behind the prompt.
        name = text.split(maxsplit=1)[0].lower() if text.strip() else ''
        command = self._commands_by_name.get(name)
        return command is not None and command.runs_while_busy

    async def run_command_text(self, text: str) -> RunCommandResult:
        try:
            parts = shlex.split(text)
        except ValueError as e:
            await self._text_displayer.display_text(f'Invalid command syntax: {e}')
            return RunCommandResult.FAILURE

        if not parts:
            return RunCommandResult.FAILURE

        cmd = parts[0].lower()
        argv = parts[1:]

        command = self._commands_by_name.get(cmd)
        if not command:
            await self._text_displayer.display_text(f'Unknown command: {cmd}')
            return RunCommandResult.FAILURE

        ctx = CommandContext(
            print=self._text_displayer.display_text,
        )

        await command.run(ctx, argv)

        return RunCommandResult.SUCCESS
