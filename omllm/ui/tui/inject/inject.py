from omcore import inject as inj

from ..config import TuiConfig
from .rendering import bind_rendering
from ...inject.inject import bind_ui


##


def bind_tui(config: TuiConfig) -> inj.Elements:
    lst: list[inj.Elemental] = [
        inj.bind(TuiConfig, to_const=config),

        bind_ui(config),

        bind_rendering(config),
    ]

    return inj.as_elements(*lst)
