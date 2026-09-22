from omcore.argparse import all as ap

from ... import agent as agn
from .base import CommandContext
from .classes import CommandClass


##


class CompactCommand(CommandClass):
    """
    Compacts the agent's context now: the older part of the conversation is summarized for the model, the transcript
    itself untouched. Any words given are instructions for the summary - what it is to keep, what it may leave out.
    """

    def __init__(
            self,
            *,
            agent: agn.Agent,
            compaction: agn.ContextCompactionRunner,
    ) -> None:
        super().__init__()

        self._agent = agent
        self._compaction = compaction

    @property
    def description(self) -> str | None:
        return 'Summarizes the older part of the conversation for the model.'

    def _configure_parser(self, parser: ap.ArgumentParser) -> None:
        super()._configure_parser(parser)

        parser.add_argument('instructions', nargs='*', help='What the summary is to keep or leave out')

    async def _run_args(self, ctx: CommandContext, args: ap.Namespace) -> None:
        instructions = ' '.join(args.instructions) or None

        try:
            reduction = await self._compaction.run_compaction(self._agent, instructions=instructions)

        except agn.NoContextCompactorError:
            await ctx.print('Context compaction is not available.')
            return

        except agn.AgentBusyError:
            await ctx.print('The agent is busy. Try again once it is done.')
            return

        if reduction is None:
            await ctx.print('Nothing to compact.')
            return

        await ctx.print(f'Context compacted: {reduction.before_tokens:,} -> {reduction.after_tokens:,} tokens')
