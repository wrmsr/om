"""
What bare does with a line of input: a slash command runs on the spot, anything else goes to the agent as a prompt.

Bare has no input area apart from its scrollback - a typed line stays where it was typed - so only input which was not
typed, a boot command, is echoed, the way the minitui surface shows every submission.
"""
from .... import agent as agn
from ...commands.manager import CommandsManager
from ...commands.manager import ParseCommandError
from ..rendering import BlockTerminalTextDisplayer


##


class Prompter:
    def __init__(
            self,
            *,
            agent: agn.Agent,
            commands: CommandsManager,
            command_output: BlockTerminalTextDisplayer,
    ) -> None:
        super().__init__()

        self._agent = agent
        self._commands = commands
        self._command_output = command_output

    async def prompt(self, input: str, *, echo: bool = False) -> None:  # noqa
        if not input:
            return

        if input[0] == '/':
            if echo:
                await self._command_output.display_text(input)

            try:
                await self._commands.parse(input[1:]).run()
            except ParseCommandError as e:
                if e.message is not None:
                    await self._command_output.display_text(e.message)
            return

        await self._agent.prompt(input)
