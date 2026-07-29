import abc
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore.argparse import all as ap

from ...core import ui


##


class CommandError(Exception):
    pass


@dc.dataclass()
class ArgsCommandError(CommandError):
    command: Command
    argv: ta.Sequence[str]
    help: str

    arg_error: ap.ArgumentError | None = None


##


@dc.dataclass(frozen=True, kw_only=True)
class CommandContext:
    print: ta.Callable[[ui.CanText], ta.Awaitable[None]]


class Command(lang.Abstract):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    def description(self) -> str | None:
        return None

    @abc.abstractmethod
    def run(self, ctx: CommandContext, argv: list[str]) -> ta.Awaitable[None]:
        raise NotImplementedError


Commands = ta.NewType('Commands', ta.Sequence[Command])
