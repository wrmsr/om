from omcore import inject as inj

from .... import harness as har
from ....core import ui
from ..config import Config
from ..inject import bind_tui
from ..rendering import BlockTerminalTextDisplayer
from .input import bind_input
from .output import bind_output
from .prompting import Prompter


##


def _provide_commands_manager(
        commands: har.Commands,
        command_output: BlockTerminalTextDisplayer,
) -> har.CommandsManager:
    return har.CommandsManager(
        commands=commands,
        text_displayer=command_output,
    )


def bind_bare(config: Config) -> inj.Elements:
    return inj.as_elements(
        inj.override(
            bind_tui(config),

            # Commands write for a surface which commits blocks. Bare's stream gives their output that shape, rather
            # than running it into whatever follows - the prompt, say.
            inj.bind(_provide_commands_manager, singleton=True),
        ),

        bind_input(config),
        bind_output(config),

        inj.bind(Prompter, singleton=True),

        inj.bind(ui.RaiseQuitSignal(SystemExit)),
        inj.bind(ui.QuitSignal, to_key=ui.RaiseQuitSignal),
    )
