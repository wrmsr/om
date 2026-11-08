from omcore import inject as inj

from ....core import ui
from ...paths import AgentCwdDisplayPathResolver
from ..config import TuiConfig
from .text import TextRowsRenderer


##


def _provide_text_rendering_options(paths: AgentCwdDisplayPathResolver) -> ui.TextRenderingOptions:
    return ui.TextRenderingOptions(paths=paths)


def bind_rendering(config: TuiConfig) -> inj.Elements:
    return inj.as_elements(
        inj.bind(AgentCwdDisplayPathResolver, singleton=True),
        inj.bind(ui.TextRenderingOptions, singleton=True, to_fn=_provide_text_rendering_options),

        inj.bind(TextRowsRenderer, singleton=True),
    )
