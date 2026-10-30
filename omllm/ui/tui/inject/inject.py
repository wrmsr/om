from omcore import inject as inj

from ...inject.inject import bind_ui
from ..config import TuiConfig
from .rendering import bind_rendering


##


def bind_tui(config: TuiConfig) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(TuiConfig, to_const=config),

        bind_ui(config),

        bind_rendering(config),
    ]

    return inj.as_elements(*lst)
