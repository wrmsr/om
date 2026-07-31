import enum
import typing as ta

from omcore import check
from omcore.formats import json5
from omcore.formats.json import all as json
from omcore.formats.json.rendering import JsonRenderer

from .types import CanText
from .types import ConcatText
from .types import JsonText
from .types import JsonTextStyle
from .types import StrText
from .types import StyleText
from .types import Text
from .types import TextStyle


##


class JsonTokenKind(enum.Enum):
    KEY = enum.auto()
    STRING = enum.auto()
    NUMBER = enum.auto()
    LITERAL = enum.auto()


def _classify_json_token(o: ta.Any, state: JsonRenderer.State) -> JsonTokenKind | None:
    if state is JsonRenderer.State.KEY:
        return JsonTokenKind.KEY

    elif o is None or isinstance(o, bool):
        return JsonTokenKind.LITERAL

    elif isinstance(o, str):
        return JsonTokenKind.STRING

    elif isinstance(o, (int, float)):
        return JsonTokenKind.NUMBER

    else:
        return None


class _JsonTokenOut:
    """Adapts JsonRenderer's pre/post style-marker stream into flat (kind, str) runs fed to a callback."""

    def __init__(self, write: ta.Callable[[JsonTokenKind | None, str], None]) -> None:
        super().__init__()

        self._write = write
        self._kinds: list[JsonTokenKind] = []

    class _Op(ta.NamedTuple):  # noqa
        mode: ta.Literal['open', 'close']
        kind: JsonTokenKind

    @classmethod
    def style(cls, o: ta.Any, state: JsonRenderer.State) -> tuple[ta.Any, ta.Any] | None:
        if (kind := _classify_json_token(o, state)) is None:
            return None

        return (cls._Op('open', kind), cls._Op('close', kind))

    def write(self, s: ta.Any) -> None:
        if isinstance(s, self._Op):
            if s.mode == 'open':
                self._kinds.append(s.kind)
            elif s.mode == 'close':
                check.state(self._kinds.pop() is s.kind)
            else:
                raise ValueError(s.mode)

        elif isinstance(s, str):
            self._write(self._kinds[-1] if self._kinds else None, s)

        else:
            raise TypeError(s)


def render_json_tokens(
        obj: ta.Any,
        style: JsonTextStyle = JsonTextStyle.DEFAULT,
        *,
        write: ta.Callable[[JsonTokenKind | None, str], None],
) -> None:
    """
    Renders obj as json into a stream of write((kind, str)) run callbacks. Kinds are the honest semantic classification
    - what, if anything, they look like is entirely up to the consuming frontend. Unset style attrs render as their
    zero-values - neutral mode, plain (non-five) json, no multiline strings.
    """

    cls: ta.Any
    if style.five:
        cls = json5.Json5Renderer
    else:
        cls = JsonRenderer

    kw: dict[str, ta.Any] = {}

    match style.mode:
        case 'pretty':
            kw.update(json.PRETTY_KWARGS)
        case 'compact':
            kw.update(json.COMPACT_KWARGS)
        case None:
            pass
        case _:
            raise ValueError(style.mode)

    if style.multiline_strings:
        kw.update(multiline_strings=True)

    if style.unquote_idents:
        kw.update(unquote_ident_keys=True)

    out = _JsonTokenOut(write)
    kw.update(style=out.style)

    cls(out, cls.Config(**kw)).render(obj)


##


# The default styling of json rendered down to the Text layer - key and string coloring only, via the deliberately dumb
# TextColor channel. Frontends wanting richer json coloring render JsonText nodes themselves via render_json_tokens.
_JSON_TOKEN_TEXT_STYLES: ta.Mapping[JsonTokenKind, TextStyle] = {
    JsonTokenKind.KEY: TextStyle(color='blue'),
    JsonTokenKind.STRING: TextStyle(color='green'),
}


def render_obj_json_text(
        obj: ta.Any,
        style: JsonTextStyle = JsonTextStyle.DEFAULT,
) -> Text:
    lst: list[CanText] = []

    def write(kind: JsonTokenKind | None, s: str) -> None:
        if kind is not None and (sty := _JSON_TOKEN_TEXT_STYLES.get(kind)) is not None:
            lst.append(StyleText(StrText(s), sty))
        else:
            lst.append(s)

    render_json_tokens(obj, style, write=write)

    return Text.of(*lst)


def render_json_texts(
        root: Text,
        style: JsonTextStyle = JsonTextStyle.DEFAULT,
) -> Text:
    def rec(cur: Text) -> CanText:
        if isinstance(cur, StrText):
            return cur

        elif isinstance(cur, StyleText):
            inner = Text.of(rec(cur.c))

            if not inner:
                return inner

            if isinstance(inner, StyleText):
                return StyleText(inner.c, cur.y.merge(inner.y))

            return StyleText(inner, cur.y)

        elif isinstance(cur, ConcatText):
            return [rec(ch) for ch in cur.l]

        elif isinstance(cur, JsonText):
            return render_obj_json_text(cur.v, style.merge(cur.y))

        else:
            # Foreign leaves (DiffText, MarkdownText, ...) pass through untouched - this only rewrites JsonText nodes.
            return cur

    return Text.of(rec(root))
