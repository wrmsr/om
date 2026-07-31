"""
TODO:
 - finish markdown impl lol
"""
import typing as ta

from omcore import cached
from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh


with lang.auto_proxy_import(globals()):
    import difflib


type CanText = ta.Union[  # noqa
    Text,
    str,
    ta.Sequence[CanText],
]

type TextColor = ta.Literal[
    'red',
    'green',
    'yellow',
    'blue',
]


##


@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(cache_hash=True, default_repr_fn=lang.opt_repr)
@msh.update_object_options(field_defaults=msh.FieldOptions(omit_if=lang.is_none))
class TextStyle(lang.Final):
    DEFAULT: ta.ClassVar[TextStyle]

    color: TextColor | None = None

    bold: bool | None = None
    italic: bool | None = None

    def merge(self, child: TextStyle) -> TextStyle:
        """Overlays child onto self - child's set attributes win."""

        return TextStyle(
            color=child.color if child.color is not None else self.color,
            bold=child.bold if child.bold is not None else self.bold,
            italic=child.italic if child.italic is not None else self.italic,
        )


TextStyle.DEFAULT = TextStyle()


##


@msh.set_polymorphic_from_subclasses(naming=msh.Naming.SNAKE, strip_suffix=True)
@dc.dataclass(frozen=True)
class Text(lang.Abstract, lang.Sealed):
    _BLANK: ta.ClassVar[StrText]

    @classmethod
    def blank(cls) -> StrText:
        check.is_(cls, Text, 'Method must not be accessed through subclasses.')

        return cls._BLANK

    @classmethod
    def of(cls, *objs: CanText) -> Text:
        check.is_(cls, Text, 'Method must not be accessed through subclasses.')

        if not objs:
            return cls._BLANK

        if len(objs) == 1 and isinstance(o0 := objs[0], Text):
            if not o0:
                return cls._BLANK
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
                # Should normally be handled by stack expansion before this point. Kept here so future
                # node-normalization hooks have one safe sink.
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
                # Style(DEFAULT, x) unwrapping is handled in the stack loop, and Style(Style(..)) chains are rejected
                # at construction.
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
            return cls._BLANK

        if len(out) == 1:
            return out[0]

        return ConcatText(tuple(out))

    @classmethod
    def str_of(cls, obj: CanText) -> str:
        check.is_(cls, Text, 'Method must not be accessed through subclasses.')

        if isinstance(obj, str):
            return obj

        else:
            return str(cls.of(obj))

    #

    def join(
            self: CanText,
            items: ta.Iterable[CanText],
    ) -> Text:
        delim = Text.of(self)

        if not delim:
            return Text.of(*items)

        return Text.of(*lang.interleave(delim, map(Text.of, items)))

    def style(
            self: CanText,
            *,
            color: TextColor | None = None,

            bold: bool | None = None,
            italic: bool | None = None,
    ) -> Text:
        x = Text.of(self)

        if not x:
            return Text._BLANK

        if (
                color is None and
                bold is None and
                italic is None
        ):
            return x

        y = TextStyle(
            color=color,
            bold=bold,
            italic=italic,
        )

        if isinstance(x, StyleText):
            # Chains collapse: the new style applies 'outside' the existing one, so the existing (inner) style's set
            # attrs win, matching the render semantics nested StyleTexts had before they were rejected.
            return StyleText(x.c, y.merge(x.y))

        return StyleText(x, y)

    #

    @lang.cached_function
    def _render_str(self) -> str:
        from .plain import render_plain_text  # function-local to avoid an import cycle with the renderer modules

        return render_plain_text(self)

    def __str__(self) -> str:
        # Implicit special-method lookup bypasses instance dicts, so a cached_function directly on __str__ would rebind
        # and recompute on every str() call - delegate to a normally-accessed cached method instead.
        return self._render_str()


##


@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True, terse_repr=True)
@msh.update_object_options(unwrap_if_single_field=True)
class StrText(Text, lang.Final):
    s: str

    def __bool__(self) -> bool:
        return bool(self.s)


Text._BLANK = StrText('')  # noqa


#


@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True)
@msh.update_object_options(unwrap_if_single_field=True)
class ConcatText(Text, lang.Final):
    l: ta.Sequence[Text]

    def __post_init__(self) -> None:
        last_was_str = False
        for c in check.not_empty(self.l):
            check.arg(bool(c))
            check.not_isinstance(c, ConcatText)

            is_str = isinstance(c, StrText)
            check.arg(not (last_was_str and is_str))
            last_was_str = is_str

    #

    def __repr__(self) -> str:
        return f'{self.__class__.__name__}({list(self.l)!r})'


##


@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True, terse_repr=True)
class StyleText(Text, lang.Final):
    c: Text
    y: TextStyle = TextStyle.DEFAULT

    #

    def __post_init__(self) -> None:
        check.arg(bool(self.c))
        check.not_isinstance(self.c, StyleText)


##


@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True, terse_repr=True)
@msh.update_object_options(unwrap_if_single_field=True)
class JsonText(Text, lang.Final):
    v: ta.Any


##


@dc.dataclass(frozen=True)
class BlockText(Text, lang.Abstract):
    """Marker for nodes which render as isolated multiline blocks rather than inline character runs."""


#


@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True, terse_repr=True)
@msh.update_object_options(unwrap_if_single_field=True)
class MarkdownText(BlockText, lang.Final):
    s: str

    def __bool__(self) -> bool:
        return bool(self.s)


##


@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(cache_hash=True)
@msh.update_object_options(field_defaults=msh.FieldOptions(omit_if=lang.is_none))
class DiffText(BlockText, lang.Final):
    """
    An old->new text change, displayed as a unified diff. Carries the texts (the honest data); the rendering is derived
    by the frontends.
    """

    old: str
    new: str

    path: str | None = None

    def __bool__(self) -> bool:
        return self.old != self.new

    @cached.property
    def diff_lines(self) -> ta.Sequence[str]:
        return tuple(difflib.unified_diff(
            self.old.splitlines(keepends=True),
            self.new.splitlines(keepends=True),
            fromfile=self.path if self.path is not None else 'old',
            tofile=self.path if self.path is not None else 'new',
        ))
