import abc
import enum
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


class CommandContextPrinter(ta.Protocol):
    def __call__(self, *texts: ui.CanText) -> ta.Awaitable[None]: ...


@dc.dataclass(frozen=True, kw_only=True)
class CommandContext:
    print: CommandContextPrinter


class RunCommandResult(enum.StrEnum):
    SUCCESS = 'success'
    FAILURE = 'failure'


class Command(lang.Abstract):
    @property
    @abc.abstractmethod
    def name(self) -> str:
        raise NotImplementedError

    @property
    def description(self) -> str | None:
        return None

    @property
    def can_run_while_busy(self) -> bool:
        return False

    @abc.abstractmethod
    def run(self, ctx: CommandContext, argv: list[str]) -> ta.Awaitable[RunCommandResult | None]:
        raise NotImplementedError


Commands = ta.NewType('Commands', ta.Sequence[Command])
