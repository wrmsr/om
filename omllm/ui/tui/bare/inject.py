from omcore import inject as inj

from ....core import ui
from ...commands.base import Commands
from ...commands.manager import CommandsManager
from ...inject.inject import UiInjector
from ...inject.inject import bind_injector_import
from ..config import TuiConfig
from ..inject import bind_tui
from ..rendering.text import BlockTerminalTextDisplayer
from .input import bind_input
from .output import bind_output
from .prompting import Prompter


##


def _provide_commands_manager(
        commands: Commands,
        command_output: BlockTerminalTextDisplayer,
) -> CommandsManager:
    return CommandsManager(
        commands=commands,
        text_displayer=command_output,
    )


def bind_bare(config: TuiConfig) -> inj.Elements:
    return inj.as_elements(
        bind_tui(
            config,

            agent_ui_rewriter=inj.overrider(
                # Commands write for a surface which commits blocks. Bare's stream gives their output that shape, rather
                # than running it into whatever follows - the prompt, say.
                inj.bind(_provide_commands_manager, singleton=True),

                bind_injector_import(UiInjector, BlockTerminalTextDisplayer),
            ),
        ),

        bind_input(config),
        bind_output(config),

        inj.bind(Prompter, singleton=True),

        inj.bind(ui.RaiseQuitSignal(SystemExit)),
        inj.bind(ui.QuitSignal, to_key=ui.RaiseQuitSignal),
    )
