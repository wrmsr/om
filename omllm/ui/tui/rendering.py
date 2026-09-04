import io
import shutil
import sys

from omcore import lang
from omcore.text import diffs
from omcore.text import styled as st
from omdev.tui import diff as df
from omdev.tui import minitui as mt

from ...core import ui


##


UI_TEXT_THEME = mt.DEFAULT_THEME.extend({
    'text.color.red': st.StylePatch(fg=mt.TEXT_ERROR),
    'text.color.green': st.StylePatch(fg=mt.SUCCESS),
    'text.color.yellow': st.StylePatch(fg=mt.WARNING),
    'text.color.blue': st.StylePatch(fg=mt.TEXT_PRIMARY),

    'json.key': st.StylePatch(fg=mt.TEXT_PRIMARY),
    'json.string': st.StylePatch(fg=mt.STRING_GREEN),
    'json.number': st.StylePatch(fg=mt.TEXT_WARNING),
    'json.literal': st.StylePatch(fg=mt.TEXT_PRIMARY),
})

UI_DIFF_THEME = mt.Theme(df.DIFF_STYLE_THEME.as_dict())


def _wrap_segment_rows(
        rows: mt.SegmentRows,
        width: int,
) -> list[list[mt.Segment]]:
    out: list[list[mt.Segment]] = []
    for row in rows:
        out.extend(mt.wrap_segments(row, width) if row else [[]])
    return out


def _resolve_segment_rows(
        rows: mt.SegmentRows,
        *,
        theme: mt.Theme,
        base: mt.Style | None = None,
) -> list[list[mt.Segment]]:
    return [
        [
            mt.Segment(segment.text, theme.resolve(segment.style, base))
            for segment in row
        ]
        for row in rows
    ]


def _block_base(block: ui.StyledTextBlock) -> mt.Style:
    return UI_TEXT_THEME.resolve_refs(block.styles)


def render_text_part_rows(
        part: ui.StyledTextPart,
        width: int,
) -> list[list[mt.Segment]]:
    """Render one target-neutral UI text part into width-safe, fully resolved minitui rows."""

    if width < 1:
        raise ValueError(width)

    if isinstance(part, st.StyledText):
        return _wrap_segment_rows(
            mt.styled_text_to_segment_lines(part, theme=UI_TEXT_THEME),
            width,
        )

    if not isinstance(part, ui.StyledTextBlock):
        raise TypeError(part)

    block = part.block
    base = _block_base(part)

    if isinstance(block, ui.MarkdownText):
        rows = mt.render_markdown_blocks(
            mt.parse_markdown_with(mt.get_markdown_stream(), block.s),
            width,
            highlighter=mt.highlight_code,
        )
        return _resolve_segment_rows(rows, theme=UI_TEXT_THEME, base=base)

    if isinstance(block, ui.DiffText):
        if width < 20:
            rows = mt.render_markdown_block(
                mt.MdCode('diff', tuple(line.rstrip('\n') for line in block.diff_lines)),
                width,
                highlighter=mt.highlight_code,
            )
            return _resolve_segment_rows(rows, theme=UI_TEXT_THEME, base=base)

        document = df.render_diff_document(
            diffs.parse_patch(''.join(block.diff_lines)),
            width=width,
        )
        return [
            mt.styled_text_to_segment_lines(line, theme=UI_DIFF_THEME, base=base)[0]
            for line in document.lines
        ]

    raise TypeError(block)


def render_text_rows(
        rendering: ui.StyledTextRendering,
        width: int,
) -> list[list[mt.Segment]]:
    """Render a complete mixed inline/block UI text result into minitui rows."""

    rows: list[list[mt.Segment]] = []
    previous: ui.StyledTextPart | None = None
    for part in rendering.parts:
        # A trailing empty row is the cursor position after an inline newline. The following part begins on that row;
        # extending blindly would manufacture an additional blank line.
        if isinstance(previous, st.StyledText) and previous.plain.endswith('\n'):
            rows.pop()
        rows.extend(render_text_part_rows(part, width))
        previous = part
    return rows


##


class TerminalTextRenderer(ui.TextRenderer[str]):
    """Render UI text to a cold ANSI string without constructing a minitui driver or event loop."""

    def __init__(
            self,
            options: ui.TextRenderingOptions | None = None,
            *,
            width: int = 80,
            color_depth: mt.ColorDepth | None = mt.ColorDepth.TRUE,
            styled_renderer: ui.StyledTextRenderer | None = None,
    ) -> None:
        super().__init__()

        if width < 1:
            raise ValueError(width)
        if color_depth is not None and not isinstance(color_depth, mt.ColorDepth):
            raise TypeError(color_depth)

        self._width = width
        self._color_depth = color_depth
        self._styled_renderer = styled_renderer if styled_renderer is not None else ui.StyledTextRenderer(options)

    def render(self, *ts: ui.CanText) -> str:
        rendering = self._styled_renderer.render(*ts)

        out = io.StringIO()
        has_output = False
        ends_with_newline = False

        def write(text: str) -> None:
            nonlocal has_output, ends_with_newline
            if text:
                out.write(text)
                has_output = True
                ends_with_newline = text.endswith('\n')

        for part in rendering.parts:
            is_block = isinstance(part, ui.StyledTextBlock)
            if is_block and has_output and not ends_with_newline:
                write('\n')

            if isinstance(part, st.StyledText):
                if self._color_depth is None:
                    write(part.plain)
                else:
                    write(mt.render_ansi_styled_text(
                        part,
                        theme=UI_TEXT_THEME,
                        depth=self._color_depth,
                    ))
            else:
                rows = render_text_part_rows(part, self._width)
                if self._color_depth is None:
                    write('\n'.join(mt.segments_text(row) for row in rows) + '\n')
                else:
                    write(mt.render_ansi_segment_rows(
                        rows,
                        depth=self._color_depth,
                        trailing_newline=True,
                    ))

        return out.getvalue()


class TerminalTextDisplayer(ui.TextDisplayer):
    """Write cold terminal-rendered UI text to a file, defaulting to stdout."""

    def __init__(
            self,
            *,
            file: lang.SupportsWrite[str] | None = None,
            renderer: TerminalTextRenderer | None = None,
    ) -> None:
        super().__init__()

        self._file = file if file is not None else sys.stdout

        if renderer is None:
            isatty = getattr(self._file, 'isatty', None)
            terminal = bool(isatty()) if callable(isatty) else False
            renderer = TerminalTextRenderer(
                width=shutil.get_terminal_size((80, 24)).columns if terminal else 80,
                color_depth=mt.detect_color_depth() if terminal else None,
            )
        self._renderer = renderer

    async def display_text(self, *texts: ui.CanText) -> None:
        self._file.write(self._renderer.render(*texts))


def build_terminal_text_displayer() -> TerminalTextDisplayer:
    return TerminalTextDisplayer()
