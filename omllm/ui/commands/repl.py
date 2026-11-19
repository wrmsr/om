"""
The repl switch commands - `/py`, `/js`, `/bash`, `/chat` - over a frontend-provided `ReplModeSwitcher`.
Frontend-neutral: a frontend with a repl binds a switcher and these; one without binds neither.
"""
import abc
import typing as ta

from omcore import lang
from omdev import repl

from .base import Command
from .base import CommandContext


##


class ReplSwitchError(Exception):
    """Carries the message for the user."""


class ReplModeSwitcher(lang.Abstract):
    @property
    @abc.abstractmethod
    def names(self) -> ta.Sequence[str]:
        raise NotImplementedError

    @abc.abstractmethod
    def switch(self, name: str | None) -> ta.Awaitable[None]:
        """Put the input into the named repl, or back to the chat for None. Raises ReplSwitchError when it cannot."""

        raise NotImplementedError

    @abc.abstractmethod
    def submit_to(self, name: str | None, text: str) -> ta.Awaitable[None]:
        raise NotImplementedError


##


class _ReplSwitchCommand(Command, lang.Abstract):
    _target: ta.ClassVar[str | None] = None

    def __init__(self, *, switcher: ReplModeSwitcher) -> None:
        super().__init__()

        self._switcher = switcher

    @property
    def can_run_while_busy(self) -> bool:
        return True

    async def run(
            self,
            ctx: CommandContext,
            args: str | lang.SequenceNotStr[str] | None = None,
    ) -> None:
        try:
            if args:
                if isinstance(args, str):
                    args_text = args
                else:
                    args_text = ' '.join(args)
                await self._switcher.submit_to(self._target, args_text)
            else:
                await self._switcher.switch(self._target)
        except ReplSwitchError as e:
            await ctx.print(str(e))


class PyCommand(_ReplSwitchCommand):
    _target = repl.DEFAULT_PYTHON_NAME

    @property
    def description(self) -> str:
        return 'Switches the input to the python repl.'


class JsCommand(_ReplSwitchCommand):
    _target = repl.DEFAULT_JAVASCRIPT_NAME

    @property
    def description(self) -> str:
        return 'Switches the input to the javascript repl.'


class BashCommand(_ReplSwitchCommand):
    _target = repl.DEFAULT_BASH_NAME

    @property
    def description(self) -> str:
        return 'Switches the input to a bash shell where the tools run.'


class ChatCommand(_ReplSwitchCommand):
    _target = None

    @property
    def description(self) -> str:
        return 'Returns the input to the chat.'
