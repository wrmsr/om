import typing as ta

from omdev.tui import rich

from .json import JsonTextRendering
from .json import render_obj_json_text
from .rendering import TextRenderer
from .rendering import TextRenderingOptions
from .rendering import squash_markdown_text
from .rendering import summarize_diff_text
from .text import CanText
from .text import ConcatText
from .text import DiffText
from .text import JsonText
from .text import MarkdownText
from .text import StrText
from .text import StyleText
from .text import Text
from .text import TextStyle


##


class RichTextRenderer(TextRenderer[ta.Any]):
    """
    Renders a Text tree to a rich renderable: a rich.Text of correctly style-merged inline runs when no blocks are
    present, otherwise a rich.Group interleaving inline runs with block renderables.
    """

    def __init__(
            self,
            options: TextRenderingOptions | None = None,
            *,
            markdown_code_theme: ta.Any | None = None,
    ) -> None:
        super().__init__()

        self._options = options if options is not None else TextRenderingOptions()
        self._markdown_code_theme = markdown_code_theme

    #

    def _to_rich_style(self, s: TextStyle) -> rich.Style | None:
        if (
                s.color is None and
                s.bold is None and
                s.italic is None
        ):
            return None

        return rich.Style(
            color=s.color,
            bold=s.bold,
            italic=s.italic,
        )

    def _render_markdown(self, n: MarkdownText) -> ta.Any:
        kw: dict[str, ta.Any] = {}
        if self._markdown_code_theme is not None:
            kw.update(code_theme=self._markdown_code_theme)

        return rich.Markdown(n.s, **kw)

    def _render_diff(self, n: DiffText, sty: TextStyle) -> rich.Text:
        # TODO: use omdev.tui.rich.diff - needs a renderable-returning, filesystem-free variant.
        dt = rich.Text()

        for l in n.diff_lines:
            if not l.endswith('\n'):
                l += '\n'

            if l.startswith('+'):
                dt.append(l, style=rich.Style(color='green'))
            elif l.startswith('-'):
                dt.append(l, style=rich.Style(color='red'))
            elif l.startswith('@@'):
                dt.append(l, style=rich.Style(color='cyan'))
            else:
                dt.append(l, style=self._to_rich_style(sty))

        return dt

    def render(self, t: CanText) -> ta.Any:
        root = Text.of(t)

        compact = self._options.density == 'compact'

        parts: list[ta.Any] = []
        cur = rich.Text()

        def flush() -> None:
            nonlocal cur
            if cur.plain:
                parts.append(cur)
                cur = rich.Text()

        stack: list[tuple[Text, TextStyle]] = [(root, TextStyle.DEFAULT)]
        while stack:
            (n, sty) = stack.pop()

            if not n:
                continue

            if isinstance(n, StrText):
                cur.append(n.s, style=self._to_rich_style(sty))

            elif isinstance(n, ConcatText):
                stack.extend((c, sty) for c in reversed(n.l))

            elif isinstance(n, StyleText):
                stack.append((n.c, sty.merge(n.y)))

            elif isinstance(n, JsonText):
                stack.append((render_obj_json_text(n.v, JsonTextRendering(mode=self._options.density)), sty))

            elif isinstance(n, MarkdownText):
                if compact:
                    cur.append(squash_markdown_text(n), style=self._to_rich_style(sty))
                else:
                    flush()
                    parts.append(self._render_markdown(n))

            elif isinstance(n, DiffText):
                if compact:
                    cur.append(summarize_diff_text(n), style=self._to_rich_style(sty))
                else:
                    flush()
                    parts.append(self._render_diff(n, sty))

            else:
                raise TypeError(n)

        if not parts:
            return cur

        flush()
        if len(parts) == 1:
            return parts[0]
        return rich.Group(*parts)
