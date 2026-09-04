"""
HTML rendering of UI text as self-contained fragments with baked-in inline styles: inline runs through the shared styled
html renderer, markdown blocks through pdcmark, and diff blocks as preformatted styled diff documents.

This exists for things like styled transcript exports. It is deliberately not the live web frontend's path - that ships
markdown and diff sources to the browser for native javascript rendering rather than prerendering them in python.
"""
import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore.text import diffs
from omcore.text import pdcmark
from omcore.text import styled as st
from omcore.text.pdcmark.rendering import html as pdcmark_html

from .rendering import TextRenderer
from .rendering import TextRenderingOptions
from .styled import StyledTextBlock
from .styled import StyledTextRenderer
from .themes import UI_TEXT_STYLE_THEME
from .types import CanText
from .types import DiffText
from .types import MarkdownText


with lang.auto_proxy_import(globals()):
    from omdev.tui import diff as tdiff
    from omdev.tui.diff import themes as tdiff_themes


##


# Model output is GFM-flavored. Whole blocks are rendered at once, so forward reference links may as well resolve.
_MARKDOWN_OPTIONS = dc.replace(pdcmark.GFM, prescan_refdefs=True)

_HTML_CODE_BLOCK = pdcmark.FencedCodeBlock('html')


def literalize_raw_markdown_html(events: ta.Iterable[pdcmark.Event]) -> list[pdcmark.Event]:
    """
    Rewrites raw html events into literal text: html blocks become `html` fenced code blocks and inline html becomes
    plain text.

    The markdown here is untrusted model output headed for a browser, and pdcmark's html renderer otherwise writes raw
    html through verbatim. This mirrors minitui, which shows html blocks as code.
    """

    out: list[pdcmark.Event] = []
    for e in events:
        if isinstance(e, pdcmark.Start) and isinstance(e.tag, pdcmark.HtmlBlock):
            out.append(pdcmark.Start(e.offset, _HTML_CODE_BLOCK))

        elif isinstance(e, pdcmark.End) and isinstance(e.tag, pdcmark.HtmlBlock):
            out.append(pdcmark.End(e.offset, _HTML_CODE_BLOCK))

        elif isinstance(e, (pdcmark.Html, pdcmark.InlineHtml)):
            out.append(pdcmark.Text(e.offset, e.text))

        else:
            out.append(e)

    return out


def render_markdown_html(s: str) -> str:
    """Renders a markdown source string to html with raw html literalized."""

    return pdcmark_html.render_html(literalize_raw_markdown_html(pdcmark.parse(s, _MARKDOWN_OPTIONS)))


##


class HtmlTextRenderer(TextRenderer[str]):
    """
    Renders UI text to an html fragment with baked-in inline css.

    Inline runs are wrapped in `white-space: pre-wrap` spans so literal whitespace survives whatever container they
    land in, markdown blocks become normal-flow html, and diff blocks become fixed-width `<pre>` documents. Consecutive
    fragments concatenate seamlessly, like the plain and terminal renderers' strings.
    """

    def __init__(
            self,
            options: TextRenderingOptions | None = None,
            *,
            theme: st.StyleTheme | None = None,
            diff_width: int = 120,
            styled_renderer: StyledTextRenderer | None = None,
    ) -> None:
        super().__init__()

        check.arg(diff_width >= 20)

        self._theme = theme if theme is not None else UI_TEXT_STYLE_THEME
        self._diff_width = diff_width
        self._styled_renderer = styled_renderer if styled_renderer is not None else StyledTextRenderer(options)

    def _render_inline(self, text: st.StyledText) -> str:
        return f'<span style="white-space:pre-wrap">{st.render_html(text, theme=self._theme)}</span>'

    def _render_markdown(self, block: MarkdownText, base: st.ResolvedStyle) -> str:
        # Markdown carries its own newlines between tags, so a pre-wrap ancestor must not get to interpret them.
        css = 'white-space:normal'
        if base_css := st.style_to_css(base):
            css = f'{css};{base_css}'

        return f'<div style="{css}">{render_markdown_html(block.s)}</div>'

    def _render_diff(self, block: DiffText, base: st.ResolvedStyle) -> str:
        document = tdiff.render_diff_document(
            diffs.parse_patch(''.join(block.diff_lines)),
            width=self._diff_width,
        )

        # The diff's own colors win over any inherited ones so its rows stay coherent on any page, while inherited flags
        # like italic still apply.
        ambient = base.apply(st.StylePatch(
            fg=tdiff_themes.CODE_FOREGROUND,
            bg=tdiff_themes.DIFF_BACKGROUND,
        ))

        rendered = st.render_html(document, theme=tdiff.DIFF_STYLE_THEME, base=ambient)
        return f'<pre style="{st.style_to_css(ambient)}">{rendered}</pre>'

    def _render_block(self, part: StyledTextBlock) -> str:
        block = part.block
        base = self._theme.resolve_refs(part.styles)

        if isinstance(block, MarkdownText):
            return self._render_markdown(block, base)

        if isinstance(block, DiffText):
            return self._render_diff(block, base)

        raise TypeError(block)

    def render(self, *ts: CanText) -> str:
        parts = self._styled_renderer.render(*ts).parts

        out: list[str] = []
        for i, part in enumerate(parts):
            if isinstance(part, st.StyledText):
                # A trailing newline ahead of a block is the cursor's move onto the block's first row. The block breaks
                # the line itself, so keeping it would manufacture a blank line.
                if part.plain.endswith('\n') and i + 1 < len(parts) and isinstance(parts[i + 1], StyledTextBlock):
                    part = part.slice(0, -1)

                if part:
                    out.append(self._render_inline(part))

            elif isinstance(part, StyledTextBlock):
                out.append(self._render_block(part))

            else:
                raise TypeError(part)

        return ''.join(out)


##


@lang.cached_function
def _default_renderer() -> HtmlTextRenderer:
    return HtmlTextRenderer()


def render_html_text(t: CanText) -> str:
    return _default_renderer().render(t)
