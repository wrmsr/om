# ruff: noqa: UP006 UP007 UP037 UP045
# @om-lite
"""
Programmatic authoring of TOML documents, with control over layout, comments and spacing, rendered through the same
`TomlValueRenderer` and `TomlStyle` used by in-place `TomlDocument` edits so that generated and edited files share one
style.
"""
import typing as ta

from .parser import TomlDocument
from .parser import TomlDocumentError
from .parser import TomlInline
from .parser import TomlMultiline
from .parser import TomlParseFloat
from .parser import TomlRaw
from .parser import TomlStyle
from .parser import TomlValueRenderer
from .parser import toml_parse_document


TomlHeaderPath = ta.Union[str, 'TomlRaw', ta.Sequence[ta.Union[str, 'TomlRaw']]]  # ta.TypeAlias


##


class TomlBuilder:
    """
    Builds a TOML document line by line: comments, blank lines, table headers, and key/value pairs, in the order they
    are added.

    Header paths given as strings are split on dots, so `table('tool.om')` writes `[tool.om]`; give a sequence of parts
    to use a part containing a dot. Pair keys given as strings are single (quoted as needed) parts; give a sequence for
    a dotted key. Values may be wrapped in `TomlInline`, `TomlMultiline`, or `TomlRaw` to control their rendering.

    Before a table header the style's blank lines between tables are inserted unless blank lines were already added
    explicitly, so blanks, comments and tables compose into groupings such as:

        b.comment('##').comment('section').table('tool.thing', {'k': 1})
        b.blank(2).comment('#').table('tool.other', comments=['directly above the header'])
    """

    def __init__(
            self,
            *,
            style: ta.Optional[TomlStyle] = None,
            newline: str = '\n',
    ) -> None:
        super().__init__()

        self._renderer = TomlValueRenderer(style, newline=newline)
        self._newline = newline

        self._lines: ta.List[str] = []

    @property
    def style(self) -> TomlStyle:
        return self._renderer.style

    @property
    def renderer(self) -> TomlValueRenderer:
        return self._renderer

    #

    @classmethod
    def _split_header_path(cls, path: TomlHeaderPath) -> ta.Tuple[ta.Union[str, TomlRaw], ...]:
        if isinstance(path, str):
            return tuple(path.split('.'))
        if isinstance(path, TomlRaw):
            return (path,)
        return tuple(path)

    def _trailing_blank_lines(self) -> int:
        n = 0
        for ln in reversed(self._lines):
            if ln:
                break
            n += 1
        return n

    #

    def blank(self, n: int = 1) -> 'TomlBuilder':
        """Adds blank lines."""

        self._lines.extend([''] * n)
        return self

    def comment(self, text: str = '') -> 'TomlBuilder':
        """Adds comment lines: each line of `text` is written as is if it already starts with '#', else prefixed."""

        for ln in (text.split('\n') if text else ['']):
            self._lines.append(self._renderer.render_comment(ln))
        return self

    def raw(self, text: str) -> 'TomlBuilder':
        """Adds verbatim source lines."""

        self._lines.extend(text.splitlines())
        return self

    def separate(self) -> 'TomlBuilder':
        """Ensures the style's blank lines between tables follow any content, unless blank lines are already present."""

        if self._lines and not self._trailing_blank_lines():
            self.blank(self._renderer.style.blank_lines_between_tables)
        return self

    def table(
            self,
            path: TomlHeaderPath,
            values: ta.Optional[ta.Mapping[ta.Any, ta.Any]] = None,
            *,
            array: bool = False,
            comments: ta.Optional[ta.Sequence[str]] = None,
    ) -> 'TomlBuilder':
        """
        Starts a `[path]` (or, if `array`, a `[[path]]`) section, separated from preceding content, with any given
        comment lines directly above its header and any given key/value pairs below it.
        """

        r = self._renderer
        key = self._split_header_path(path)
        if not key:
            raise TomlDocumentError('Table paths must be non-empty')

        self.separate()
        for c in (comments or ()):
            self._lines.append(r.render_comment(c))
        self._lines.append(('[[' if array else '[') + r.render_key(key) + (']]' if array else ']'))

        for k, v in (values or {}).items():
            self.pair(k, v)

        return self

    def pair(
            self,
            key: ta.Any,
            value: ta.Any,
            *,
            layout: ta.Optional[str] = None,
            comment: ta.Optional[str] = None,
    ) -> 'TomlBuilder':
        """
        Adds a `key = value` line, optionally forcing an 'inline' or 'multiline' layout and adding a trailing comment.
        """

        r = self._renderer

        if isinstance(key, (str, TomlRaw, int)):
            key_text = r.render_key_part(key)
        else:
            key_text = r.render_key(key)

        if layout == 'inline':
            value = TomlInline(value)
        elif layout == 'multiline':
            value = TomlMultiline(value)
        elif layout is not None:
            raise TomlDocumentError(f'Unknown layout {layout!r}')

        line = key_text + ' = ' + r.render_value(value)
        if comment is not None:
            line += '  ' + r.render_comment(comment)
        self._lines.append(line)

        return self

    #

    def render(self) -> str:
        if not self._lines:
            return ''
        return self._newline.join(self._lines) + self._newline

    def document(self, *, parse_float: TomlParseFloat = float) -> TomlDocument:
        """Parses the built source into a `TomlDocument` carrying the builder's style, validating it in the process."""

        return toml_parse_document(self.render(), parse_float=parse_float, style=self._renderer.style)


##


def toml_dumps(
        obj: ta.Mapping[ta.Any, ta.Any],
        *,
        style: ta.Optional[TomlStyle] = None,
        newline: str = '\n',
) -> str:
    """
    Renders a mapping as a TOML document. Top-level mapping values become `[table]` sections, their keys interpreted as
    header paths (strings split on dots) and any mappings nested within them rendered as inline tables. Other top-level
    values become root key/value pairs, written before any section. Wrap a top-level mapping in `TomlInline` to write
    it as a root inline table instead. Use a `TomlBuilder` directly for nested sections, comments, or custom spacing.
    """

    b = TomlBuilder(style=style, newline=newline)

    sections = []
    for k, v in obj.items():
        if isinstance(v, ta.Mapping):
            sections.append((k, v))
        else:
            b.pair(k, v)

    for k, v in sections:
        b.table(k, v)

    return b.render()
