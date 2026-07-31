import functools
import typing as ta

from omcore import dataclasses as dc
from omdev.tui import rich

from .display import TextDisplayer
from .json import JsonTokenKind
from .json import render_json_tokens
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
from .types import TextStyle


##


@dc.dataclass(frozen=True, kw_only=True)
class RichJsonStyles:
    """
    Rich styles applied per rendered json token kind - values are rich style specs (rich.Style instances or style
    strings like 'bold #57A5E2'), or None to leave that kind unstyled. Defaults match the dumb TextColor-channel
    styling of the Text-layer json rendering.
    """

    key: ta.Any | None = 'blue'
    string: ta.Any | None = 'green'
    number: ta.Any | None = None
    literal: ta.Any | None = None


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
            json_styles: RichJsonStyles | None = None,
    ) -> None:
        super().__init__()

        self._options = options if options is not None else TextRenderingOptions()
        self._markdown_code_theme = markdown_code_theme

        js = json_styles if json_styles is not None else RichJsonStyles()
        self._json_token_styles: ta.Mapping[JsonTokenKind, ta.Any] = {
            k: rich.Style.parse(v) if isinstance(v, str) else v
            for k, v in [
                (JsonTokenKind.KEY, js.key),
                (JsonTokenKind.STRING, js.string),
                (JsonTokenKind.NUMBER, js.number),
                (JsonTokenKind.LITERAL, js.literal),
            ]
            if v is not None
        }

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

    def _append_json_token(
            self,
            out: rich.Text,
            base: rich.Style | None,
            kind: JsonTokenKind | None,
            s: str,
    ) -> None:
        ksty = self._json_token_styles.get(kind) if kind is not None else None

        sty: ta.Any
        if base is None:
            sty = ksty
        elif ksty is None:
            sty = base
        else:
            sty = base + ksty

        out.append(s, style=sty)

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
                render_json_tokens(
                    n.v,
                    resolve_json_text_style(self._options, n.y),
                    write=functools.partial(self._append_json_token, cur, self._to_rich_style(sty)),
                )

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


##


class RichTextDisplayer(TextDisplayer):
    """Displays texts by rendering them through a RichTextRenderer and printing them to a rich Console."""

    def __init__(
            self,
            *,
            console: rich.Console | None = None,
            renderer: RichTextRenderer | None = None,
    ) -> None:
        super().__init__()

        self._console = console if console is not None else rich.Console()
        self._renderer = renderer if renderer is not None else RichTextRenderer()

    async def display_text(self, text: CanText) -> None:
        self._console.print(self._renderer.render(text))
