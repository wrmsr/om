from omcore import inject as inj

from ....core import ui
from ..config import Config
from ..inject import bind_tui
from .input import bind_input
from .output import bind_output


##


def bind_bare(config: Config) -> inj.Elements:
    return inj.as_elements(
        bind_tui(config),

        bind_input(config),
        bind_output(config),

        inj.bind(ui.RaiseQuitSignal(SystemExit)),
        inj.bind(ui.QuitSignal, to_key=ui.RaiseQuitSignal),
    )
