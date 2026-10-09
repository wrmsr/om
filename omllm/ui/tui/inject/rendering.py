from omcore import inject as inj

from ....core import ui
from ..rendering import TextRowsRenderer
from ..types import TargetCwd


##


def _provide_text_rendering_options(cwd: TargetCwd) -> ui.TextRenderingOptions:
    return ui.TextRenderingOptions(cwd=cwd.v)


def bind_rendering() -> inj.Elements:
    return inj.as_elements(
        inj.bind(ui.TextRenderingOptions, singleton=True, to_fn=_provide_text_rendering_options),

        inj.bind(TextRowsRenderer, singleton=True),
    )
