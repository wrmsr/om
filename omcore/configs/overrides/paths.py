import json
import re
import typing as ta

from ... import dataclasses as dc
from ... import lang
from .literals import RawScalar


OverridePath: ta.TypeAlias = ta.Sequence['PathSegment']


##


class PathSegment(lang.Abstract, lang.Sealed):
    pass


@dc.dataclass(frozen=True)
class KeySegment(PathSegment, lang.Final):
    """
    `.name`, `."name"`, or `["name"]`. An unquoted integer key (`.0`, `.-1`) is treated as an index when it is applied
    to a list, making it the bracketless spelling of an IndexSegment.
    """

    name: str
    quoted: bool = False


@dc.dataclass(frozen=True)
class IndexSegment(PathSegment, lang.Final):
    """`[0]`, `[-1]`."""

    index: int


@dc.dataclass(frozen=True)
class AppendSegment(PathSegment, lang.Final):
    """`[+]` or `.+` - the not yet existing element past the end of a list."""


@dc.dataclass(frozen=True)
class SelectSegment(PathSegment, lang.Final):
    """`[name=enc]`, `[spec.id=3]` - the single list element with the given value at the given keys."""

    keys: ta.Sequence[str] = dc.xfield(coerce=tuple)
    value: RawScalar = dc.xfield()


##


BARE_KEY_PAT = re.compile(r'[A-Za-z0-9_-]+')
INT_PAT = re.compile(r'-?\d+')


def try_parse_int_key(seg: KeySegment) -> int | None:
    if seg.quoted or not INT_PAT.fullmatch(seg.name):
        return None
    return int(seg.name)


def _render_key(name: str, *, quoted: bool = False) -> str:
    # Quoting only matters to an otherwise bare key where it would otherwise be taken as an index.
    if not BARE_KEY_PAT.fullmatch(name) or (quoted and INT_PAT.fullmatch(name)):
        return json.dumps(name)
    return name


def render_segment(seg: PathSegment, *, first: bool = False) -> str:
    if isinstance(seg, KeySegment):
        if (k := _render_key(seg.name, quoted=seg.quoted))[0] == '"':
            return f'[{k}]'
        return k if first else f'.{k}'

    elif isinstance(seg, IndexSegment):
        return f'[{seg.index}]' if first else f'.{seg.index}'

    elif isinstance(seg, AppendSegment):
        return '[+]' if first else '.+'

    elif isinstance(seg, SelectSegment):
        v = json.dumps(seg.value.text) if seg.value.quoted else seg.value.text
        return f'[{".".join(_render_key(k) for k in seg.keys)}={v}]'

    else:
        raise TypeError(seg)


def render_path(path: OverridePath) -> str:
    """Renders a path in the grammar it was parsed from, preferring the bracketless spellings."""

    return ''.join(render_segment(seg, first=not i) for i, seg in enumerate(path))


def describe_path(path: OverridePath) -> str:
    return repr(render_path(path)) if path else 'the root'
