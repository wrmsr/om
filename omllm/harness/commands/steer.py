from omcore.argparse import all as ap

from ... import agent as agn
from .base import CommandContext
from .classes import CommandClass


##


class SteerCommand(CommandClass):
    def __init__(self, *, agent: agn.Agent) -> None:
        super().__init__()

        self._agent = agent

    @property
    def description(self) -> str:
        return 'Sends instructions to the running agent at its next turn boundary.'

    @property
    def runs_while_busy(self) -> bool:
        return True

    def _configure_parser(self, parser: ap.ArgumentParser) -> None:
        super()._configure_parser(parser)

        parser.add_argument('message', nargs='+')

    async def _run_args(self, ctx: CommandContext, args: ap.Namespace) -> None:
        if not self._agent.is_prompting:
            await ctx.print('No prompt is running. Send a normal prompt to start one.')
            return

        message = ' '.join(args.message).strip()
        if not message:
            await ctx.print('Steering instructions cannot be empty.')
            return

        self._agent.steer(message)
        await ctx.print('Steering queued for the next turn boundary.')
