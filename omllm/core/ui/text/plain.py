import io

from omcore import lang
from omcore.text import styled as st

from .rendering import TextRenderer
from .rendering import TextRenderingOptions
from .styled import StyledTextBlock
from .styled import StyledTextRenderer
from .types import CanText
from .types import DiffText
from .types import MarkdownText


##


class PlainTextRenderer(TextRenderer[str]):
    def __init__(self, options: TextRenderingOptions | None = None) -> None:
        super().__init__()

        self._options = options if options is not None else TextRenderingOptions()
        self._styled_renderer = StyledTextRenderer(self._options)

    #

    def render(self, *ts: CanText) -> str:
        out = io.StringIO()
        last = ''

        def write(s: str) -> None:
            nonlocal last
            if s:
                out.write(s)
                last = s[-1]

        def begin_block() -> None:
            if last and last != '\n':
                write('\n')

        for part in self._styled_renderer.render(*ts).parts:
            if isinstance(part, st.StyledText):
                write(part.plain)

            elif isinstance(part, StyledTextBlock):
                node = part.block

                if isinstance(node, MarkdownText):
                    begin_block()
                    write(node.s)
                    if last != '\n':
                        write('\n')

                elif isinstance(node, DiffText):
                    begin_block()
                    for line in node.diff_lines:
                        write(line if line.endswith('\n') else line + '\n')

                else:
                    raise TypeError(node)

            else:
                raise TypeError(part)

        return out.getvalue()


##


@lang.cached_function
def _default_renderer() -> PlainTextRenderer:
    return PlainTextRenderer()


def render_plain_text(t: CanText) -> str:
    return _default_renderer().render(t)
