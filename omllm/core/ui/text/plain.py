import io

from omcore import lang

from .json import render_obj_json_text
from .rendering import TextRenderer
from .rendering import TextRenderingOptions
from .rendering import resolve_json_text_style
from .rendering import squash_markdown_text
from .rendering import summarize_diff_text
from .types import CanText
from .types import ConcatText
from .types import DiffText
from .types import JsonText
from .types import MarkdownText
from .types import StrText
from .types import StyleText
from .types import Text


##


class PlainTextRenderer(TextRenderer[str]):
    def __init__(self, options: TextRenderingOptions | None = None) -> None:
        super().__init__()

        self._options = options if options is not None else TextRenderingOptions()

    #

    def render(self, t: CanText) -> str:
        root = Text.of(t)

        compact = self._options.density == 'compact'

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

        stack: list[Text] = [root]
        while stack:
            n = stack.pop()

            if not n:
                continue

            if isinstance(n, StrText):
                write(n.s)

            elif isinstance(n, ConcatText):
                stack.extend(reversed(n.l))

            elif isinstance(n, StyleText):
                stack.append(n.c)

            elif isinstance(n, JsonText):
                stack.append(render_obj_json_text(n.v, resolve_json_text_style(self._options, n.y)))

            elif isinstance(n, MarkdownText):
                if compact:
                    write(squash_markdown_text(n))
                else:
                    begin_block()
                    write(n.s)
                    if last != '\n':
                        write('\n')

            elif isinstance(n, DiffText):
                if compact:
                    write(summarize_diff_text(n))
                else:
                    begin_block()
                    for l in n.diff_lines:
                        write(l if l.endswith('\n') else l + '\n')

            else:
                raise TypeError(n)

        return out.getvalue()


##


@lang.cached_function
def _default_renderer() -> PlainTextRenderer:
    return PlainTextRenderer()


def render_plain_text(t: CanText) -> str:
    return _default_renderer().render(t)
