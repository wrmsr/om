import typing as ta

from .types import _BLANK_TEXT
from .types import CanText
from .types import ConcatText
from .types import StrText
from .types import StyleText
from .types import Text
from .types import TextStyle


##


def normalize_text(*objs: CanText) -> Text:
    if not objs:
        return _BLANK_TEXT

    if len(objs) == 1 and isinstance(o0 := objs[0], Text):
        if not o0:
            return _BLANK_TEXT
        if not (isinstance(o0, StyleText) and o0.y == TextStyle.DEFAULT):
            return o0

    out: list[Text] = []
    pending_strs: list[str] = []

    def flush_strs() -> None:
        if pending_strs:
            out.append(StrText(''.join(pending_strs)))
            pending_strs.clear()

    def emit_node(t: Text) -> None:
        if isinstance(t, StrText):
            if t.s:
                pending_strs.append(t.s)

        elif isinstance(t, ConcatText):
            # Should normally be handled by stack expansion before this point. Kept here so future node-normalization
            # hooks have one safe sink.
            for c in t.l:
                emit_node(c)

        else:
            if not t:
                return

            flush_strs()

            # Future style hook:
            #
            #   - adjacent equal Style nodes maybe merge their children
            #
            # Style(DEFAULT, x) unwrapping is handled in the stack loop, and Style(Style(..)) chains are rejected at
            # construction.
            out.append(t)

    stack: list[CanText] = list(reversed(objs))

    while stack:
        o = stack.pop()

        if isinstance(o, str):
            if o:
                pending_strs.append(o)

        elif isinstance(o, StrText):
            if o.s:
                pending_strs.append(o.s)

        elif isinstance(o, ConcatText):
            stack.extend(reversed(o.l))

        elif isinstance(o, StyleText) and o.y == TextStyle.DEFAULT:
            # Style(DEFAULT, x) -> x
            stack.append(o.c)

        elif isinstance(o, Text):
            emit_node(o)

        elif isinstance(o, ta.Sequence):
            stack.extend(reversed(o))

        else:
            raise TypeError(o)

    flush_strs()

    if not out:
        return _BLANK_TEXT

    if len(out) == 1:
        return out[0]

    return ConcatText(tuple(out))
