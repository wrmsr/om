"""
Type-directed resolution of raw value literals into concrete values: the shape of the target, not the spelling of the
value, decides what a bare scalar is. `1.10` is the string `'1.10'` for a string and the float `1.1` for a float, and is
only ever guessed at where the shape is anything - or is unknown, and guessing has been permitted.
"""
import typing as ta

from .errors import OverrideError
from .errors import OverrideValueError
from .errors import UnhandledOverrideShapeError
from .errors import render_suggestion
from .literals import RawList
from .literals import RawMap
from .literals import RawNode
from .literals import RawScalar
from .literals import guess_raw
from .paths import IndexSegment
from .paths import KeySegment
from .paths import OverridePath
from .paths import describe_path
from .shapes import AnyShape
from .shapes import ChoiceShape
from .shapes import ListShape
from .shapes import MapShape
from .shapes import ObjectShape
from .shapes import OptionalShape
from .shapes import ScalarShape
from .shapes import Shape
from .shapes import TaggedShape
from .shapes import TupleShape
from .shapes import UnionShape
from .shapes import UnknownShape
from .shapes import describe_shape
from .shapes import unlazy_shape


##


def _parse_bool(text: str) -> bool:
    if text == 'true':
        return True
    elif text == 'false':
        return False
    else:
        raise ValueError(text)


def _parse_int(text: str) -> int:
    try:
        return int(text)
    except ValueError:
        return int(text, 0)


_SCALAR_PARSERS: ta.Mapping[type, ta.Callable[[str], ta.Any]] = {
    bool: _parse_bool,
    int: _parse_int,
    float: float,
    str: str,
}


def parse_scalar(text: str, ty: type) -> ta.Any:
    """Raises ValueError if the text is not a valid spelling of the given type."""

    if (fn := _SCALAR_PARSERS.get(ty)) is None:
        raise ValueError(text)
    return fn(text)


def scalar_matches(v: ta.Any, raw: RawScalar) -> bool:
    """Whether a raw scalar spells the given concrete scalar value."""

    if isinstance(v, str):
        return raw.text == v
    elif raw.quoted:
        return False
    elif v is None:
        return raw.text == 'null'
    elif isinstance(v, (bool, int, float)):
        try:
            return parse_scalar(raw.text, type(v)) == v
        except ValueError:
            return False
    else:
        return False


##


class ValueResolver:
    def __init__(
            self,
            *,
            guess_unknown: bool = False,
    ) -> None:
        super().__init__()

        self._guess_unknown = guess_unknown

    def _check_guessable(self, shape: Shape, path: OverridePath) -> AnyShape:
        if not self._guess_unknown:
            raise UnhandledOverrideShapeError(
                f'Cannot produce a value at {describe_path(path)}: its shape is {describe_shape(shape)}, and guessing '
                f'is not enabled',
            )
        return AnyShape()

    def _error(self, raw: RawNode, shape: Shape, path: OverridePath) -> OverrideValueError:
        if isinstance(raw, RawScalar):
            got = f'{"string " if raw.quoted else ""}{raw.text!r}'
            if raw.structure_error is not None:
                got += f' ({raw.structure_error})'
        elif isinstance(raw, RawList):
            got = 'a list'
        else:
            got = 'a map'
        return OverrideValueError(f'Expected {describe_shape(shape)} at {describe_path(path)}, got {got}')

    #

    def _resolve_scalar(self, raw: RawNode, shape: ScalarShape, path: OverridePath) -> ta.Any:
        if isinstance(raw, (RawList, RawMap)):
            # A string taking the entirety of a value takes it verbatim, whatever it happens to look like.
            if shape.ty is str and raw.text is not None:
                return raw.text

        elif isinstance(raw, RawScalar):
            if shape.ty is str:
                return raw.text
            if not raw.quoted:
                try:
                    return parse_scalar(raw.text, shape.ty)
                except ValueError:
                    pass

        raise self._error(raw, shape, path)

    def _resolve_choice(self, raw: RawNode, shape: ChoiceShape, path: OverridePath) -> ta.Any:
        if not isinstance(raw, RawScalar):
            raise self._error(raw, shape, path)

        for v in shape.values:
            if scalar_matches(v, raw):
                return v

        sug = render_suggestion(raw.text, [v for v in shape.values if isinstance(v, str)])
        raise OverrideValueError(f'{self._error(raw, shape, path)}{sug}')

    def _resolve_union(self, raw: RawNode, shape: UnionShape, path: OverridePath) -> ta.Any:
        for alt in shape.alternatives:
            try:
                return self.resolve(raw, alt, path)
            except UnhandledOverrideShapeError:
                raise
            except OverrideError:
                pass
        raise self._error(raw, shape, path)

    #

    def _resolve_list(self, raw: RawNode, shape: ListShape | TupleShape, path: OverridePath) -> list:
        if not isinstance(raw, RawList):
            raise self._error(raw, shape, path)

        ess: ta.Sequence[Shape]
        if isinstance(shape, TupleShape):
            if len(raw.items) != len(ess := shape.elements):
                raise OverrideValueError(
                    f'Expected exactly {len(ess)} elements at {describe_path(path)}, got {len(raw.items)}',
                )
        else:
            ess = [shape.element] * len(raw.items)

        return [
            self.resolve(e, es, (*path, IndexSegment(i)))
            for i, (e, es) in enumerate(zip(raw.items, ess, strict=True))
        ]

    def _resolve_fields(
            self,
            items: ta.Iterable[tuple[str, RawNode]],
            shape: MapShape | ObjectShape | AnyShape,
            path: OverridePath,
    ) -> dict[str, ta.Any]:
        ret: dict[str, ta.Any] = {}
        for k, v in items:
            vs: Shape
            if isinstance(shape, MapShape):
                vs = shape.value
            elif isinstance(shape, ObjectShape):
                try:
                    vs = shape.fields[k]
                except KeyError:
                    if not shape.open:
                        raise OverrideValueError(
                            f'Unknown key {k!r} at {describe_path(path)}{render_suggestion(k, shape.fields)}',
                        ) from None
                    vs = AnyShape()
            else:
                vs = shape
            ret[k] = self.resolve(v, vs, (*path, KeySegment(k, quoted=True)))
        return ret

    def _resolve_tagged(self, raw: RawNode, shape: TaggedShape, path: OverridePath) -> dict[str, ta.Any]:
        if not isinstance(raw, RawMap):
            raise self._error(raw, shape, path)

        def get_tagged(tag: str) -> Shape:
            try:
                return shape.by_tag[tag]
            except KeyError:
                raise OverrideValueError(
                    f'Unknown tag {tag!r} at {describe_path(path)}{render_suggestion(tag, shape.by_tag)}',
                ) from None

        if (tf := shape.tag_field) is None:
            if len(raw.items) != 1:
                raise OverrideValueError(
                    f'Expected a map of exactly one tag at {describe_path(path)}, got {len(raw.items)}',
                )
            [(tag, v)] = raw.items
            return {tag: self.resolve(v, get_tagged(tag), (*path, KeySegment(tag, quoted=True)))}

        if (tv := dict(raw.items).get(tf)) is None:
            raise OverrideValueError(f'Missing {tf!r} tag at {describe_path(path)}')
        tag = self._resolve_choice(tv, ChoiceShape(list(shape.by_tag)), (*path, KeySegment(tf, quoted=True)))

        ts = unlazy_shape(get_tagged(tag))
        if not isinstance(ts, (MapShape, ObjectShape, AnyShape)):
            ts = self._check_guessable(ts, path)
        return {tf: tag, **self._resolve_fields([(k, v) for k, v in raw.items if k != tf], ts, path)}

    #

    def resolve(self, raw: RawNode, shape: Shape, path: OverridePath = ()) -> ta.Any:
        shape = unlazy_shape(shape)

        if isinstance(shape, UnknownShape):
            shape = self._check_guessable(shape, path)

        if isinstance(shape, AnyShape):
            return guess_raw(raw)

        elif isinstance(shape, ScalarShape):
            return self._resolve_scalar(raw, shape, path)

        elif isinstance(shape, ChoiceShape):
            return self._resolve_choice(raw, shape, path)

        elif isinstance(shape, OptionalShape):
            if isinstance(raw, RawScalar) and not raw.quoted and raw.text == 'null':
                return None
            return self.resolve(raw, shape.inner, path)

        elif isinstance(shape, UnionShape):
            return self._resolve_union(raw, shape, path)

        elif isinstance(shape, (ListShape, TupleShape)):
            return self._resolve_list(raw, shape, path)

        elif isinstance(shape, (MapShape, ObjectShape)):
            if not isinstance(raw, RawMap):
                raise self._error(raw, shape, path)
            return self._resolve_fields(raw.items, shape, path)

        elif isinstance(shape, TaggedShape):
            return self._resolve_tagged(raw, shape, path)

        else:
            raise TypeError(shape)
