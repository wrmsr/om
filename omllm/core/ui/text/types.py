import typing as ta

from omcore import cached
from omcore import check
from omcore import dataclasses as dc
from omcore import lang
from omcore import marshal as msh


with lang.auto_proxy_import(globals()):
    import difflib

    from . import normalize
    from . import plain


type CanText = ta.Union[  # noqa
    Text,
    str,
    ta.Sequence[CanText],
]


##


# A deliberately dumb, limited signaling channel for the wide range of internal machinery that needs to tell the user
# something - render an ASK permission as yellow, DENY as red, ALLOW as green. The canned handful of colors is a
# conscious choice to not (yet?) abstract it into semantic notions like WARNING / INFO / BAD / MAYBE-BAD and
# immediately wind up reinventing CSS.
type TextColor = ta.Literal[
    'red',
    'green',
    'yellow',
    'blue',
]


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
            color=lang.opt_coalesce(child.color, self.color),
            bold=lang.opt_coalesce(child.bold, self.bold),
            italic=lang.opt_coalesce(child.italic, self.italic),
        )


TextStyle.DEFAULT = TextStyle()


##


@msh.set_polymorphic_from_subclasses(naming=msh.Naming.SNAKE, suffix_stripping=msh.SuffixStripping.REQUIRED)
@dc.dataclass(frozen=True)
class Text(lang.Abstract, lang.Sealed):
    """
    A small, closed family of composable nodes for presenting text to a (probably human) end user, renderable to bare
    text, rich terminal text, html, and other future targets. This is *not* the representation of messages sent to and
    from llm backends - it is the ui-facing channel from internal machinery (a tool executor, for example) to whatever
    is displaying things to the user.

    The inline nodes (StrText / ConcatText / StyleText / JsonText) are meant to be fairly user-friendly, cover common
    simple cases, and be suitable for 'inline' rendering (like a bottom status bar in a tui), with a deliberately dumb,
    limited styling channel (see TextColor). The block nodes (BlockText subclasses like MarkdownText and DiffText) are
    for big, isolated, semantically meaningful payloads which merely ride the same channels - renderers receive them
    whole and decide their presentation entirely themselves.
    """

    @classmethod
    def blank(cls) -> StrText:
        check.is_(cls, Text, 'Method must not be accessed through subclasses.')

        return _BLANK_TEXT

    @classmethod
    def of(cls, *objs: CanText) -> Text:
        check.is_(cls, Text, 'Method must not be accessed through subclasses.')

        return normalize.normalize_text(*objs)

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
            return _BLANK_TEXT

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
        return plain.render_plain_text(self)

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


_BLANK_TEXT = StrText('')  # noqa


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


@dc.dataclass(frozen=True, kw_only=True)
@dc.extra_class_params(cache_hash=True, default_repr_fn=lang.opt_repr)
@msh.update_object_options(field_defaults=msh.FieldOptions(omit_if=lang.is_none))
class JsonTextStyle(lang.Final):
    DEFAULT: ta.ClassVar[JsonTextStyle]

    mode: ta.Literal['pretty', 'compact'] | None = None

    five: bool | None = None
    multiline_strings: bool | None = None
    unquote_idents: bool | None = None

    def __post_init__(self) -> None:
        if (
            self.multiline_strings or
            self.unquote_idents
        ):
            check.arg(bool(self.five))

    def merge(self, child: JsonTextStyle) -> JsonTextStyle:
        """Overlays child onto self - child's set attributes win."""

        return JsonTextStyle(
            mode=lang.opt_coalesce(child.mode, self.mode),
            five=lang.opt_coalesce(child.five, self.five),
            multiline_strings=lang.opt_coalesce(child.multiline_strings, self.multiline_strings),
            unquote_idents=lang.opt_coalesce(child.unquote_idents, self.unquote_idents),
        )


JsonTextStyle.DEFAULT = JsonTextStyle()


@dc.dataclass(frozen=True)
@dc.extra_class_params(cache_hash=True, terse_repr=True)
@msh.update_object_options(unwrap_if_single_field=True)
@msh.update_field_options('y', omit_if=lambda y: y == JsonTextStyle.DEFAULT)
class JsonText(Text, lang.Final):
    v: ta.Any
    y: JsonTextStyle = JsonTextStyle.DEFAULT


##


@dc.dataclass(frozen=True)
class BlockText(Text, lang.Abstract):
    """Marker for nodes which render as isolated multiline blocks rather than inline character runs."""


##


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
            fromfile=lang.coalesce(self.path, 'old'),
            tofile=lang.coalesce(self.path, 'new'),
        ))
