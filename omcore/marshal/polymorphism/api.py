import dataclasses as dc
import typing as ta

from ... import check
from ... import lang
from ... import metadata as md
from ..api.configs import Config
from ..api.errors import MarshalError
from ..api.naming import Naming
from ..api.naming import translate_name


T = ta.TypeVar('T')


##


class PolymorphismTagError(MarshalError):
    pass


class PolymorphismSubtypeError(MarshalError):
    pass


##


class TypeTagging(Config, lang.Abstract, lang.Sealed):
    pass


# Fieldless frozen dataclass so tagging values compare by value - they participate in value-keyed PolymorphismSpecs.
@dc.dataclass(frozen=True)
class WrapperTypeTagging(TypeTagging, lang.Final):
    pass


@dc.dataclass(frozen=True)
class FieldTypeTagging(TypeTagging, lang.Final):
    field: str


##


class AUTO_STRIP_SUFFIX(lang.Marker):  # noqa
    pass


##


@dc.dataclass(frozen=True)
class SubtypeInfo(lang.Final):
    """One concrete participant in a polymorphism, bound to its wire tag."""

    ty: type
    tag: str
    alts: ta.AbstractSet[str] = frozenset()

    def __post_init__(self) -> None:
        check.state(not lang.is_abstract(self.ty))
        check.non_empty_str(self.tag)

        if not isinstance(self.alts, frozenset):
            object.__setattr__(self, 'alts', frozenset(check.not_isinstance(self.alts, str)))


@dc.dataclass(frozen=True)
class SubtypeInfos(lang.Final):
    """Collection of subtype infos with cached lookups."""

    lst: ta.Sequence[SubtypeInfo]

    def __post_init__(self) -> None:
        if not isinstance(self.lst, tuple):
            object.__setattr__(self, 'lst', tuple(self.lst))
        for i in self.lst:
            check.isinstance(i, SubtypeInfo)

    def __iter__(self) -> ta.Iterator[SubtypeInfo]:
        return iter(self.lst)

    def __len__(self) -> int:
        return len(self.lst)

    def __bool__(self) -> bool:
        return bool(self.lst)

    # The index properties are lazily built and cached - this module is api-light and cannot afford the heavy
    # dataclass/caching machinery the analogous objects FieldInfos uses.

    @property
    def by_ty(self) -> ta.Mapping[type, SubtypeInfo]:
        try:
            return self._by_ty  # type: ignore[attr-defined]
        except AttributeError:
            pass

        dct: dict[type, SubtypeInfo] = {}
        for i in self.lst:
            if i.ty in dct:
                raise PolymorphismSubtypeError(f'Duplicate subtype: {i.ty!r}')
            dct[i.ty] = i

        object.__setattr__(self, '_by_ty', dct)
        return dct

    @property
    def by_tag(self) -> ta.Mapping[str, SubtypeInfo]:
        try:
            return self._by_tag  # type: ignore[attr-defined]
        except AttributeError:
            pass

        dct: dict[str, SubtypeInfo] = {}
        for i in self.lst:
            for t in (i.tag, *i.alts):
                if t in dct:
                    raise PolymorphismSubtypeError(f'Duplicate subtype tag {t!r}: {dct[t].ty!r}, {i.ty!r}')
                dct[t] = i

        object.__setattr__(self, '_by_tag', dct)
        return dct


@dc.dataclass(frozen=True)
class Polymorphism(lang.Final):
    """The resolved product: a root and its tagged subtypes."""

    # Usually the root class, but reflected types (aliases and the like) remain legal for explicit-flavor matching.
    root: ta.Any

    subtypes: SubtypeInfos

    def __post_init__(self) -> None:
        check.isinstance(self.subtypes, SubtypeInfos)

        if isinstance(ty := self.root, type):
            for i in self.subtypes:
                check.issubclass(i.ty, ty)


##


def polymorphism_from_subtypes(
        ty: type,
        subtype_tys: ta.Iterable[type],
        *,
        naming: Naming | None = None,
        strip_suffix: bool | type[AUTO_STRIP_SUFFIX] | str = False,
) -> Polymorphism:
    subtype_tys = set(subtype_tys)

    ssx: str | None
    if strip_suffix is AUTO_STRIP_SUFFIX:
        strip_suffix = all(c.__name__.endswith(ty.__name__) for c in subtype_tys)
    if isinstance(strip_suffix, bool):
        ssx = ty.__name__ if strip_suffix else None
    elif isinstance(strip_suffix, str):
        ssx = strip_suffix
    else:
        raise TypeError(strip_suffix)

    dct: dict[str, SubtypeInfo] = {}
    for cur in subtype_tys:
        name = cur.__name__
        if ssx is not None:
            name = lang.must_remove_suffix(name, ssx)
        if naming is not None:
            name = translate_name(name, naming)
        if name in dct:
            raise PolymorphismSubtypeError(f'Duplicate subtype tag {name!r}: {dct[name].ty!r}, {cur!r}')

        dct[name] = SubtypeInfo(
            cur,
            name,
        )

    return Polymorphism(
        ty,
        SubtypeInfos(list(dct.values())),
    )


def polymorphism_from_subclasses(
        ty: type,
        *,
        naming: Naming | None = None,
        strip_suffix: bool | type[AUTO_STRIP_SUFFIX] | str = False,
) -> Polymorphism:
    return polymorphism_from_subtypes(
        ty,
        set(lang.deep_subclasses(ty, concrete_only=True)),
        naming=naming,
        strip_suffix=strip_suffix,
    )


##


@dc.dataclass(frozen=True)
class SubtypeConfig(Config, lang.Final):
    """
    Registers a class as a subtype of a polymorphic root by updating a config registry under the root's key. Resolved
    by ConfigSubtypeSource - late registrations invalidate affected handlers through the config footprint mechanism.
    """

    ty: type

    _: dc.KW_ONLY

    tag: str | None = None
    alts: ta.Sequence[str] | None = None

    def __post_init__(self) -> None:
        if self.alts is not None and not isinstance(self.alts, tuple):
            object.__setattr__(self, 'alts', tuple(check.not_isinstance(self.alts, str)))


##


@dc.dataclass(frozen=True, kw_only=True)
class _PolymorphismMetadata(md.ClassDecoratorObjectMetadata, lang.Final):
    mode: ta.Literal['subclasses'] = 'subclasses'

    type_tagging: TypeTagging = WrapperTypeTagging()
    naming: Naming | None = None
    strip_suffix: bool | type[AUTO_STRIP_SUFFIX] | str = False


def set_polymorphic_from_subclasses(
        *,
        type_tagging: TypeTagging = WrapperTypeTagging(),
        naming: Naming | None = None,
        strip_suffix: bool | type[AUTO_STRIP_SUFFIX] | str = False,
) -> ta.Callable[[type[T]], type[T]]:
    def inner(cls):
        _PolymorphismMetadata(
            mode='subclasses',
            type_tagging=type_tagging,
            naming=naming,
            strip_suffix=strip_suffix,
        )(cls)

        return cls

    return inner
