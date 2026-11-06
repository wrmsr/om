"""
UI text lowered to the json value the browser renders. A plain run is a string, a concatenation a list, and every other
node a single-keyed object:

  - `{"style": {"color": ..., "bold": ..., "italic": ...}, "c": <text>}`
  - `{"json": [[<kind or null>, <str>], ...]}` - json pre-tokenized here, its token kinds styled by the browser
  - `{"md": <source>}` - markdown, shipped as its source and rendered by the browser
  - `{"diff": {"path": <str or null>, "lines": [<unified diff line>, ...]}}`

This is the live frontend's path, as opposed to `ui.HtmlTextRenderer`'s prerendered fragments: the browser decides
what everything looks like.
"""
import typing as ta

from ...core import ui


##


# Not spelled out further: the shapes above are what the browser's renderer accepts.
WebText: ta.TypeAlias = ta.Any


class WebTextRenderer(ui.TextRenderer[WebText]):
    def __init__(self, options: ui.TextRenderingOptions | None = None) -> None:
        super().__init__()

        self._options = options if options is not None else ui.TextRenderingOptions()

    @staticmethod
    def _render_style(y: ui.TextStyle) -> dict[str, ta.Any]:
        dct: dict[str, ta.Any] = {}
        if y.color is not None:
            dct['color'] = y.color
        if y.bold is not None:
            dct['bold'] = y.bold
        if y.italic is not None:
            dct['italic'] = y.italic
        return dct

    def _render_json(self, t: ui.JsonText) -> WebText:
        tokens: list[list[ta.Any]] = []

        def write(kind: ui.JsonTokenKind | None, s: str) -> None:
            k = kind.name.lower() if kind is not None else None

            # Adjacent runs of a kind merge, so that punctuation and whitespace do not each cost a token.
            if tokens and tokens[-1][0] == k:
                tokens[-1][1] += s
            else:
                tokens.append([k, s])

        ui.render_json_tokens(t.v, ui.resolve_json_text_style(self._options, t.y), write=write)

        return {'json': tokens}

    def _render_diff(self, t: ui.DiffText) -> WebText:
        t = ui.resolve_display_diff_text(self._options, t)

        return {'diff': {
            'path': t.path,
            'lines': list(t.diff_lines),
        }}

    def _render(self, t: ui.Text) -> WebText:
        if isinstance(t, ui.StrText):
            return t.s

        elif isinstance(t, ui.ConcatText):
            return [self._render(c) for c in t.l]

        elif isinstance(t, ui.StyleText):
            return {
                'style': self._render_style(t.y),
                'c': self._render(t.c),
            }

        elif isinstance(t, ui.JsonText):
            return self._render_json(t)

        elif isinstance(t, ui.MarkdownText):
            return {'md': t.s}

        elif isinstance(t, ui.DiffText):
            return self._render_diff(t)

        else:
            raise TypeError(t)

    def render(self, *ts: ui.CanText) -> WebText:
        return self._render(ui.Text.of(*ts))
