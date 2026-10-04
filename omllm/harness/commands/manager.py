import shlex
import typing as ta

from omcore import collections as col
from omcore import dataclasses as dc

from ...core import ui
from .base import Command
from .base import CommandContext
from .base import CommandError
from .base import Commands
from .base import RunCommandResult


##


@dc.dataclass(frozen=True)
class ParsedCommand:
    command: Command
    run: ta.Callable[[], ta.Awaitable[RunCommandResult]]


@dc.dataclass()
class ParseCommandError(CommandError):
    message: ui.CanText | None = None


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

    def parse(self, text: str) -> ParsedCommand:
        try:
            parts = shlex.split(text)
        except ValueError as e:
            raise ParseCommandError(f'Invalid command syntax: {e}') from e

        if not parts:
            raise ParseCommandError('Empty command')

        cmd = parts[0].lower()
        argv = parts[1:]

        command = self._commands_by_name.get(cmd)
        if command is None:
            raise ParseCommandError(f'Unknown command: {cmd}')

        ctx = CommandContext(
            print=self._text_displayer.display_text,
        )

        async def run() -> RunCommandResult:
            if (rc := await command.run(ctx, argv)) is not None:
                return rc
            return RunCommandResult.SUCCESS

        return ParsedCommand(
            command=command,
            run=run,
        )
