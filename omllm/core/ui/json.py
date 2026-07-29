import typing as ta

from omcore import check
from omcore import dataclasses as dc
from omcore.formats import json5
from omcore.formats.json import all as json
from omcore.formats.json.rendering import JsonRenderer

from .text import CanText
from .text import ConcatText
from .text import JsonText
from .text import StrText
from .text import StyleText
from .text import Text
from .text import TextStyle


##


@dc.dataclass(frozen=True)
class JsonTextRendering:
    mode: ta.Literal['pretty', 'compact', None] = None

    _: dc.KW_ONLY

    five: bool = False
    multiline_strings: bool = False


##


class _StyleRendererOut:
    def __init__(self) -> None:
        super().__init__()

        self._stack: list[tuple[_StyleRendererOut.Op | None, list[CanText]]] = [(None, [])]

    class Op(ta.NamedTuple):  # noqa
        mode: ta.Literal['open', 'close']
        item: ta.Literal['key', 'str']

    @classmethod
    def style(cls, o: ta.Any, state: JsonRenderer.State) -> tuple[ta.Any, ta.Any] | None:
        if state is JsonRenderer.State.KEY:
            return (cls.Op('open', 'key'), cls.Op('close', 'key'))
        elif isinstance(o, str):
            return (cls.Op('open', 'str'), cls.Op('close', 'str'))
        else:
            return None

    def write(self, s: ta.Any) -> None:
        if isinstance(s, self.Op):
            if s.mode == 'open':
                self._stack.append((s, []))

            elif s.mode == 'close':
                (op, lst) = self._stack.pop()
                check.state(check.not_none(op).item == s.item)

                match s.item:
                    case 'key':
                        sty = TextStyle(color='blue')
                    case 'str':
                        sty = TextStyle(color='green')
                    case _:
                        raise ValueError(s.item)

                tx = StyleText(
                    Text.of(*lst),
                    sty,
                )

                self._stack[-1][1].append(tx)

            else:
                raise ValueError(s.mode)

        elif isinstance(s, str):
            self._stack[-1][1].append(s)

        else:
            raise TypeError(s)

    def build(self) -> Text:
        (op, lst) = check.single(self._stack)
        check.none(op)
        return Text.of(*lst)


def render_obj_json_text(
        obj: ta.Any,
        args: JsonTextRendering = JsonTextRendering(),
) -> Text:
    cls: ta.Any
    if args.five:
        cls = json5.Json5Renderer
    else:
        cls = JsonRenderer

    kw: dict[str, ta.Any] = {}
    match args.mode:
        case 'pretty':
            kw.update(json.PRETTY_KWARGS)
        case 'compact':
            kw.update(json.COMPACT_KWARGS)
        case None:
            pass
        case _:
            raise ValueError(args.mode)

    if args.multiline_strings:
        check.arg(args.five)
        kw.update(multiline_strings=True)

    out = _StyleRendererOut()
    kw.update(style=out.style)

    cls(out, **kw).render(obj)

    return out.build()


##


def render_json_texts(
        root: Text,
        args: JsonTextRendering = JsonTextRendering(),
) -> Text:
    def rec(cur: Text) -> CanText:
        if isinstance(cur, StrText):
            return cur

        elif isinstance(cur, StyleText):
            return StyleText(Text.of(rec(cur.c)), cur.y)

        elif isinstance(cur, ConcatText):
            return [rec(ch) for ch in cur.l]

        elif isinstance(cur, JsonText):
            return render_obj_json_text(cur.v, args)

        else:
            raise TypeError(cur)

    return Text.of(rec(root))
