from omcore import inject as inj

from ....core import ui
from ..rendering import TextRowsRenderer


##


def bind_rendering() -> inj.Elements:
    return inj.as_elements(
        inj.bind(ui.TextRenderingOptions()),

        inj.bind(TextRowsRenderer, singleton=True),
    )
