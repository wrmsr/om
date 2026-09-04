import functools
import typing as ta

from omcore import dataclasses as dc
from omcore import lang
from omcore.text import styled as st

from .json import JsonTokenKind
from .json import render_json_tokens
from .rendering import TextRenderer
from .rendering import TextRenderingOptions
from .rendering import resolve_json_text_style
from .rendering import squash_markdown_text
from .rendering import summarize_diff_text
from .types import BlockText
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
class StyledJsonStyles(lang.Final):
    """Semantic styles attached to rendered JSON token kinds."""

    key: st.StyleLike | None = 'json.key'
    string: st.StyleLike | None = 'json.string'
    number: st.StyleLike | None = 'json.number'
    literal: st.StyleLike | None = 'json.literal'


@dc.dataclass(frozen=True)
class StyledTextBlock(lang.Final):
    """A semantic block retained for a target-specific renderer, with its inherited inline style stack."""

    block: BlockText
    styles: tuple[st.StyleRef, ...] = ()

    def __post_init__(self) -> None:
        if not isinstance(self.block, BlockText):
            raise TypeError(self.block)

        styles = tuple(self.styles)
        if not all(isinstance(style, (st.StylePatch, st.StyleName)) for style in styles):
            raise TypeError(styles)
        object.__setattr__(self, 'styles', styles)


type StyledTextPart = st.StyledText | StyledTextBlock


@dc.dataclass(frozen=True)
class StyledTextRendering(lang.Final):
    """Target-neutral inline styled text interleaved with semantic block nodes."""

    parts: tuple[StyledTextPart, ...] = ()

    def __post_init__(self) -> None:
        parts = tuple(self.parts)
        if not all(isinstance(part, (st.StyledText, StyledTextBlock)) for part in parts):
            raise TypeError(parts)
        object.__setattr__(self, 'parts', parts)

    @property
    def is_inline(self) -> bool:
        return all(isinstance(part, st.StyledText) for part in self.parts)

    @property
    def inline(self) -> st.StyledText | None:
        """The complete styled text when no semantic blocks are present, otherwise None."""

        if not self.is_inline:
            return None
        return st.StyledText.of(*ta.cast(tuple[st.StyledText, ...], self.parts))


##


_TEXT_COLOR_STYLE_NAMES: ta.Mapping[str, st.StyleName] = {
    color: st.StyleName(f'text.color.{color}')
    for color in ('red', 'green', 'yellow', 'blue')
}


def _text_style_refs(style: TextStyle) -> tuple[st.StyleRef, ...]:
    refs: list[st.StyleRef] = []
    if style.color is not None:
        refs.append(_TEXT_COLOR_STYLE_NAMES[style.color])

    patch = st.StylePatch(
        bold=style.bold,
        italic=style.italic,
    )
    if not patch.is_empty:
        refs.append(patch)

    return tuple(refs)


def _styled(text: str, styles: ta.Iterable[st.StyleRef]) -> st.StyledText:
    out = st.StyledText(text)
    for style in styles:
        out = out.styled(style)
    return out


class StyledTextRenderer(TextRenderer[StyledTextRendering]):
    """
    Lowers the shared UI Text tree into target-neutral styled text while retaining semantic blocks for frontends.

    Compact rendering degrades blocks to inline summaries, so its result is always available through `inline`.
    """

    def __init__(
            self,
            options: TextRenderingOptions | None = None,
            *,
            json_styles: StyledJsonStyles | None = None,
    ) -> None:
        super().__init__()

        self._options = options if options is not None else TextRenderingOptions()

        json_styles = json_styles if json_styles is not None else StyledJsonStyles()
        self._json_token_styles: ta.Mapping[JsonTokenKind, st.StyleRef] = {
            kind: st.as_style_ref(style)
            for kind, style in (
                (JsonTokenKind.KEY, json_styles.key),
                (JsonTokenKind.STRING, json_styles.string),
                (JsonTokenKind.NUMBER, json_styles.number),
                (JsonTokenKind.LITERAL, json_styles.literal),
            )
            if style is not None
        }

    def _append_json_token(
            self,
            out: st.StyledTextBuilder,
            base: tuple[st.StyleRef, ...],
            kind: JsonTokenKind | None,
            text: str,
    ) -> None:
        styles = base
        if kind is not None and (token_style := self._json_token_styles.get(kind)) is not None:
            styles = (*styles, token_style)
        out.append(_styled(text, styles))

    def render(self, *ts: CanText) -> StyledTextRendering:
        root = Text.of(*ts)
        compact = self._options.density == 'compact'

        parts: list[StyledTextPart] = []
        current = st.StyledTextBuilder()

        def flush() -> None:
            if current:
                parts.append(current.build())
                current.clear()

        stack: list[tuple[Text, TextStyle]] = [(root, TextStyle.DEFAULT)]
        while stack:
            node, style = stack.pop()

            if not node:
                continue

            style_refs = _text_style_refs(style)

            if isinstance(node, StrText):
                current.append(_styled(node.s, style_refs))

            elif isinstance(node, ConcatText):
                stack.extend((child, style) for child in reversed(node.l))

            elif isinstance(node, StyleText):
                stack.append((node.c, style.merge(node.y)))

            elif isinstance(node, JsonText):
                render_json_tokens(
                    node.v,
                    resolve_json_text_style(self._options, node.y),
                    write=functools.partial(self._append_json_token, current, style_refs),
                )

            elif isinstance(node, MarkdownText):
                if compact:
                    current.append(_styled(squash_markdown_text(node), style_refs))
                else:
                    flush()
                    parts.append(StyledTextBlock(node, style_refs))

            elif isinstance(node, DiffText):
                if compact:
                    current.append(_styled(summarize_diff_text(node), style_refs))
                else:
                    flush()
                    parts.append(StyledTextBlock(node, style_refs))

            else:
                raise TypeError(node)

        flush()
        return StyledTextRendering(tuple(parts))
