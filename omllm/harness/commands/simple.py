from omcore.argparse import all as argparse

from ...core import ui
from .base import CommandContext
from .classes import CommandClass


##


class EchoCommand(CommandClass):
    def _configure_parser(self, parser: argparse.ArgumentParser) -> None:
        super()._configure_parser(parser)

        parser.add_argument('message', help='Message to echo')

    async def _run_args(self, ctx: CommandContext, args: argparse.Namespace) -> None:
        await ctx.print(args.message)


##


class QuitCommand(CommandClass):
    def __init__(
            self,
            *,
            quit_signal: ui.QuitSignal,
    ) -> None:
        super().__init__()

        self._quit_signal = quit_signal

    async def _run_args(self, ctx: CommandContext, args: argparse.Namespace) -> None:
        await self._quit_signal.quit()
