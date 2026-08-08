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


class PolymorphismSuffixError(MarshalError):
    pass


class PolymorphismSubtypeError(MarshalError):
    pass


##


@dc.dataclass(frozen=True)
class TypeTagging(Config, lang.Abstract, lang.Sealed):
    pass


@dc.dataclass(frozen=True)
class WrapperTypeTagging(TypeTagging, lang.Final):
    pass


@dc.dataclass(frozen=True)
class FieldTypeTagging(TypeTagging, lang.Final):
    field: str


#


SimpleTypeTagging: ta.TypeAlias = ta.Literal[
    'wrapper',
]


_SIMPLE_TYPE_TAGGING_MAP: ta.Mapping[SimpleTypeTagging, TypeTagging] = {
    'wrapper': WrapperTypeTagging(),
}


##


SuffixStrippingMode: ta.TypeAlias = ta.Literal[
    'required',
    'if_all',
    'if_present',
]


@dc.dataclass(frozen=True)
class SuffixStripping(Config, lang.Final):
    suffix: str | None = None  # If `None` then the suffix will implicitly be the full base name

    _: dc.KW_ONLY

    mode: SuffixStrippingMode = 'if_all'  # Matches previous 'auto' behavior


#


SimpleSuffixStripping: ta.TypeAlias = ta.Literal[
    'required',
    'if_all',
    'if_present',
]

_SIMPLE_SUFFIX_STRIPPING_MAP: ta.Mapping[SimpleSuffixStripping, SuffixStripping] = {
    'required': SuffixStripping(mode='required'),
    'if_all': SuffixStripping(mode='if_all'),
    'if_present': SuffixStripping(mode='if_present'),
}


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


def _strip_suffixes(
        suffix_stripping: SuffixStripping,
        parent_name: str,
        child_names: ta.Iterable[str],
) -> dict[str, str]:
    child_names = set(check.not_isinstance(child_names, str))
    suffix = check.non_empty_str(lang.coalesce(suffix_stripping.suffix, parent_name))

    if child_names_without := {cn for cn in child_names if not cn.endswith(suffix)}:
        match suffix_stripping.mode:
            case 'required':
                raise PolymorphismSuffixError(suffix, child_names_without)  # noqa
            case 'if_all':
                return {cn: cn for cn in child_names}

    return {cn: cn.removesuffix(suffix) for cn in child_names}


def _suffix_stripper(
        suffix_stripping: SuffixStripping | None,
        parent_name: str,
        child_names: ta.Iterable[str],
) -> ta.Callable[[str], str]:
    if suffix_stripping is None:
        return lang.identity

    return _strip_suffixes(
        suffix_stripping,
        parent_name,
        child_names,
    ).__getitem__


##


def polymorphism_from_subtypes(
        ty: type,
        subtype_tys: ta.Iterable[type],
        *,
        naming: Naming | None = None,
        suffix_stripping: SuffixStripping | None = None,
) -> Polymorphism:
    subtype_tys = set(subtype_tys)

    strip_suffix = _suffix_stripper(
        suffix_stripping,
        ty.__name__,
        {c.__name__ for c in subtype_tys},
    )

    dct: dict[str, SubtypeInfo] = {}
    for cur in subtype_tys:
        name = strip_suffix(cur.__name__)
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
        suffix_stripping: SuffixStripping | None = None,
) -> Polymorphism:
    return polymorphism_from_subtypes(
        ty,
        set(lang.deep_subclasses(ty, concrete_only=True)),
        naming=naming,
        suffix_stripping=suffix_stripping,
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


class SubtypeSource(lang.Abstract):
    """Sources are values: immutable, hashable, compared by value."""


@ta.final
@dc.dataclass(frozen=True)
class ExplicitSubtypeSource(SubtypeSource, lang.Final):
    """Carries final, already-tagged subtype infos - passes through tag derivation untouched."""

    subtypes: SubtypeInfos


@ta.final
@dc.dataclass(frozen=True)
class SubclassesSubtypeSource(SubtypeSource, lang.Final):
    """
    Deep-scans the root's subclasses at resolve time. Note the sharp edge: subclasses imported after handler
    construction are invisible until something invalidates the handler (a config change observed in its footprint, or
    a Runtime.flush()).
    """


@ta.final
@dc.dataclass(frozen=True)
class ConfigsSubtypeSource(SubtypeSource, lang.Final):
    """
    Reads `SubtypeConfig` configs registered under the root's key. The read lands in the handler's config footprint,
    so late registrations invalidate and rebuild affected handlers.
    """


@ta.final
@dc.dataclass(frozen=True)
class ManifestsSubtypeSource(SubtypeSource, lang.Final):
    """
    Collects `SubtypeManifest` entries whose (resolved) base path names the root - letting subtypes scattered across
    lazily-imported modules be discovered without importing them. Matched entries' modules are imported eagerly at
    handler construction; tags are derived from the manifests' attr (class name) strings per the spec's naming
    configuration unless explicitly overridden on the manifest.
    """


#


SimpleSubtypeSource: ta.TypeAlias = ta.Literal[
    'subclasses',
    'configs',
    'manifests',
]


_SIMPLE_SUBTYPE_SOURCE_MAP: ta.Mapping[SimpleSubtypeSource, SubtypeSource] = {
    'subclasses': SubclassesSubtypeSource(),
    'configs': ConfigsSubtypeSource(),
    'manifests': ManifestsSubtypeSource(),
}


##


@dc.dataclass(frozen=True, kw_only=True)
class _PolymorphismMetadata(md.ClassDecoratorObjectMetadata, lang.Final):
    sources: ta.Sequence[SubtypeSource]

    type_tagging: TypeTagging = WrapperTypeTagging()
    naming: Naming | None = None
    suffix_stripping: SuffixStripping | None = None


DEFAULT_POLYMORPHIC_SOURCE: ta.Final[SubtypeSource] = SubclassesSubtypeSource()


def set_polymorphic(
        *,
        source: SubtypeSource | SimpleSubtypeSource | None = None,
        sources: ta.Sequence[SubtypeSource | SimpleSubtypeSource] | None = None,

        type_tagging: TypeTagging | SimpleTypeTagging = 'wrapper',
        naming: Naming | None = None,
        suffix_stripping: SuffixStripping | SimpleSuffixStripping | None = None,
) -> ta.Callable[[type[T]], type[T]]:
    if source is not None and sources is not None:
        raise ValueError('Must not specify both `source` and `sources')
    elif source is not None:
        sources = [source]
    elif sources is None:
        sources = [DEFAULT_POLYMORPHIC_SOURCE]
    sources_ = check.not_empty(tuple(
        sts if isinstance(sts, SubtypeSource) else _SIMPLE_SUBTYPE_SOURCE_MAP[sts] for sts in sources
    ))

    if not isinstance(type_tagging, TypeTagging):
        type_tagging = _SIMPLE_TYPE_TAGGING_MAP[type_tagging]
    if suffix_stripping is not None and not isinstance(suffix_stripping, SuffixStripping):
        suffix_stripping = _SIMPLE_SUFFIX_STRIPPING_MAP[suffix_stripping]

    def inner(cls):
        _PolymorphismMetadata(
            sources=sources_,
            type_tagging=check.isinstance(type_tagging, TypeTagging),
            naming=naming,
            suffix_stripping=check.isinstance(suffix_stripping, (SuffixStripping, None)),
        )(cls)

        return cls

    return inner
